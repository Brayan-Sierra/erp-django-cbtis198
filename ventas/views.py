import io
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, DeleteView
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

from .forms import DetalleVentaForm, VentaForm
from .models import DetalleVenta, Venta
from configuracion.models import ConfiguracionERP


class VentaListView(ListView):
    model               = Venta
    template_name       = 'ventas/lista.html'
    context_object_name = 'ventas'
    paginate_by         = 20


class VentaDetailView(DetailView):
    model               = Venta
    template_name       = 'ventas/detalle.html'
    context_object_name = 'venta'
    pk_url_kwarg        = 'venta_id'


@login_required
def crear_venta(request):
    user = request.user
    
    # Si el usuario pertenece a grupos pero no tiene add_venta, denegar (Regla W09)
    # Si es el usuario básico sin grupos (Regla W08), permitir la creación
    if user.groups.exists() or user.user_permissions.exists():
        if not user.has_perm('ventas.add_venta'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

    venta_form   = VentaForm(request.POST or None)
    detalle_form = DetalleVentaForm(request.POST or None)

    if request.method == 'POST':
        if venta_form.is_valid() and detalle_form.is_valid():
            venta         = venta_form.save()
            detalle       = detalle_form.save(commit=False)
            detalle.venta = venta
            detalle.save()
            messages.success(
                request,
                f'Venta #{venta.pk} registrada. Total: ${venta.total:.2f}'
            )
            return redirect('ventas:detalle', venta_id=venta.pk)

    return render(request, 'ventas/crear.html', {
        'venta_form':   venta_form,
        'detalle_form': detalle_form,
    })


class VentaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model               = Venta
    template_name       = 'ventas/eliminar.html'
    pk_url_kwarg        = 'venta_id'
    success_url         = reverse_lazy('ventas:lista')
    permission_required = 'ventas.delete_venta'

    def form_valid(self, form):
        pk       = self.object.pk
        response = super().form_valid(form)
        messages.success(self.request, f'Venta #{pk} eliminada.')
        return response


@login_required
def venta_pdf(request, venta_id: int):
    """Genera y descarga la factura de una venta en formato PDF en memoria."""
    venta = get_object_or_404(
        Venta.objects
        .select_related('cliente')
        .prefetch_related('detalles__producto'),
        pk=venta_id
    )
    config = ConfiguracionERP.get_instance()
    
    context = {
        'venta': venta,
        'config': config,
    }

    html_string = render_to_string('ventas/factura_pdf.html', context)
    buffer = io.BytesIO()

    pisa_status = pisa.CreatePDF(html_string, dest=buffer)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF de la factura', status=500)

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{venta.pk:05d}.pdf"'
    return response