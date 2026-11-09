from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Crea los 3 grupos iniciales del sistema ERP con sus permisos RBAC.'

    def handle(self, *args, **options):
        # 1. Grupo Gerente
        gerente_group, _ = Group.objects.get_or_create(name='Gerente')
        gerente_group.permissions.set(Permission.objects.all())

        # 2. Grupo Vendedor
        vendedor_group, _ = Group.objects.get_or_create(name='Vendedor')
        permisos_vendedor = Permission.objects.filter(
            codename__in=[
                'view_producto', 'view_cliente', 'add_cliente',
                'change_cliente', 'view_venta', 'add_venta', 'change_venta',
            ]
        )
        vendedor_group.permissions.set(permisos_vendedor)

        # 3. Grupo Almacén
        almacen_group, _ = Group.objects.get_or_create(name='Almacén')
        permisos_almacen = Permission.objects.filter(
            codename__in=[
                'view_producto', 'add_producto', 'change_producto',
                'view_categoria', 'add_categoria', 'change_categoria',
                'view_proveedor', 'add_proveedor', 'change_proveedor',
            ]
        )
        almacen_group.permissions.set(permisos_almacen)

        self.stdout.write(
            self.style.SUCCESS('Grupos y permisos creados/actualizados exitosamente.')
        )
