from .models import Vale_Movimiento_Almacen, Transportista, Movimiento_EE, Movimiento_Ins, Movimiento_MP
from inventario.models import Inv_Mat_Prima
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.contrib.staticfiles import finders
import os
from io import BytesIO
import re

def export_vale(request, id_movimiento):
   data = {}
   #data['date'] = 
   #Diccionario de vale
   current_vale = {}
   inventarios = False        
   tipo = []
   vale = Vale_Movimiento_Almacen.objects.filter(consecutivo=id_movimiento)[0]
   inventarios_mp = Movimiento_MP.objects.filter(vale=vale.id) #vale.movimientos.all()
   if inventarios_mp:
      tipo.append('materias primas')
   inventarios_env = vale.movimientos_envases.all()
   if inventarios_env:
      tipo.append('envase') 
   inventarios_prod = vale.movimientos_productos.all()
   if inventarios_prod:
      tipo.append('productos')
   inventarios_ins = vale.movimientos_insumos.all()
   if inventarios_ins:
      tipo.append('insumos')
   inventarios_mp_prod = vale.mp_produccion.all()
   if inventarios_mp_prod:
      tipo.append('SolicitudMPP')
   inventarios_prod_prod = vale.productos_produccion.all()
   if inventarios_prod_prod:
      tipo.append('SolicitudPP')
   inventarios_env_env = vale.env_envasado.all()
   if inventarios_env_env:
      tipo.append('SolicitudEE')
      insumos_env = vale.ins_envasado.all()
      solicitud_env = inventarios_env_env[0].solicitud
      data['insumos_e'] = insumos_env
      data['solicitud_e'] = solicitud_env
   
   data['tipop'] = tipo
   if tipo == []:
      return HttpResponse('No se registraron movimientos de inventario con ese id')   
   else:
      data['consecutivo'] = vale.consecutivo
      if tipo == 'Solicitud':
         data['almacen'] = vale.mp_produccion.first().almacen
      else:
         data['almacen'] = vale.almacen
      #data['RestoAlmacen'] = vale.almacen.get_inv_mp()
      data['fecha'] = vale.fecha_movimiento
      data['suministrador'] = vale.suministrador
      data['origen'] = vale.origen
      data['destino'] = vale.destino 
      data['orden'] = vale.orden_No
      data['lote'] = vale.lote_No
      data['tipoi'] = vale.tipo.upper()
      data['descripcion'] = vale.descripcion if vale.descripcion else ''
      if vale.transportista:
         data['nombre_transportista'] = vale.transportista
         data['ci_transportista'] = vale.transportista_cI
      else:
         data['nombre_transportista'] = ''
         data['ci_transportista'] = ''
         data['cargo_transportista'] = ''
      data['chapa'] = vale.chapa
      data['despachado'] = vale.despachado_por
      template_src = 'movimientos/vale.html'
      template = get_template(template_src)
      context = {'data': data, 'inventarios_mp': inventarios_mp, 'inventarios_prod': inventarios_prod,
                 'inventarios_prod_prod': inventarios_prod_prod,'inventarios_mp_prod': inventarios_mp_prod, 
                 'inventarios_env': inventarios_env, 'inventarios_ins': inventarios_ins, 
                 'inventarios_env_env': inventarios_env_env, 'request': request}
      response = HttpResponse(content_type='application/pdf')
      response['Content-Disposition'] = 'attachment; filename="vale.pdf"'
      html = template.render(context)
      # create a pdf
      pisa_status = pisa.CreatePDF(
         html, dest=response, link_callback=link_callback)
      # if error then show some funny view
      if pisa_status.err:
         return HttpResponse('We had some errors <pre>' + html + '</pre>')
      return response

def export_vales(request):
    # Obtener IDs desde GET (ej. ?ids=1,2,3)
    ids_str = request.GET.get('ids', '')
    if not ids_str:
        return HttpResponse("Debe proporcionar al menos un ID")

    vale_ids = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
    if not vale_ids:
        return HttpResponse("IDs inválidos")

    vales_html = []  # Guardará el HTML renderizado de cada vale

    for id_movimiento in vale_ids:
        data = {}
        try:
            vale = Vale_Movimiento_Almacen.objects.get(consecutivo=id_movimiento)
        except Vale_Movimiento_Almacen.DoesNotExist:
            continue  # Si no existe, saltar

        tipo = []
        vale = Vale_Movimiento_Almacen.objects.filter(consecutivo=id_movimiento)[0]
        inventarios_mp = Movimiento_MP.objects.filter(vale=vale.id) #vale.movimientos.all()
        if inventarios_mp:
            tipo.append('materias primas')
        inventarios_env = vale.movimientos_envases.all()
        if inventarios_env:
            tipo.append('envase') 
        inventarios_prod = vale.movimientos_productos.all()
        if inventarios_prod:
            tipo.append('productos')
        inventarios_ins = vale.movimientos_insumos.all()
        if inventarios_ins:
            tipo.append('insumos')
        inventarios_mp_prod = vale.mp_produccion.all()
        if inventarios_mp_prod:
            tipo.append('SolicitudMPP')
        inventarios_prod_prod = vale.productos_produccion.all()
        if inventarios_prod_prod:
            tipo.append('SolicitudPP')
        inventarios_env_env = vale.env_envasado.all()
        if inventarios_env_env:
            tipo.append('SolicitudEE')
            insumos_env = vale.ins_envasado.all()
            solicitud_env = inventarios_env_env[0].solicitud
            data['insumos_e'] = insumos_env
            data['solicitud_e'] = solicitud_env
   
        # ---- LLENAR data (igual que antes) ----
        data['tipop'] = tipo
        data['consecutivo'] = vale.consecutivo
        data['almacen'] = vale.almacen if tipo != 'Solicitud' else vale.mp_produccion.first().almacen
        data['fecha'] = vale.fecha_movimiento
        data['suministrador'] = vale.suministrador or ''
        data['origen'] = vale.origen or ''
        data['destino'] = vale.destino or ''
        data['orden'] = vale.orden_No or ''
        data['lote'] = vale.lote_No or ''
        data['tipoi'] = vale.tipo.upper()
        data['descripcion'] = vale.descripcion or ''
        data['nombre_transportista'] = vale.transportista or ''
        data['ci_transportista'] = vale.transportista_cI or ''
        data['despachado'] = vale.despachado_por
        data['chapa'] = vale.chapa or ''

        # Renderizar la plantilla del vale
        template = get_template('movimientos/vale.html')
        context = {'data': data, 'inventarios_mp': inventarios_mp, 'inventarios_prod': inventarios_prod,
                 'inventarios_prod_prod': inventarios_prod_prod,'inventarios_mp_prod': inventarios_mp_prod, 
                 'inventarios_env': inventarios_env, 'inventarios_ins': inventarios_ins, 
                 'inventarios_env_env': inventarios_env_env, 'request': request}
        html_vale = template.render(context)
        vales_html.append(html_vale)

    if not vales_html:
        return HttpResponse("No se pudo generar ningún vale")

    # ---- AGRUPAR EN PAREJAS PARA DOS POR PÁGINA ----
    grouped = [vales_html[i:i+2] for i in range(0, len(vales_html), 2)]

    # ---- CONSTRUIR HTML FINAL CON CONTENEDORES POR PÁGINA ----
    pages = []
    for group in grouped:
        # Contenedor de página (tabla de una columna y dos filas)
        
        # Rellenar con los vales (si hay uno solo, la segunda fila queda vacía)
        vale1 = group[0] if len(group) > 0 else ''
        vale2 = group[1] if len(group) > 1 else ''
        
        page_html = f"""
        <table class="page-table">
            <tr>
                <td class="vale-cell">{vale1}</td>
            </tr>
            <tr>
                <td class="vale-cell">{vale2}</td>
            </tr>
        </table>
        """
        pages.append(page_html)

    # ---- ESTILOS Y ESTRUCTURA COMPLETA ----
    # Combinar todos los vales en un solo documento HTML
        # ---- ESTILOS Y ESTRUCTURA COMPLETA ----
    combined_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: letter portrait;
                margin: 0.5cm 0.5cm 0.5cm 0.5cm;
            }}
            .page-table {{
                width: 100%;
                border-collapse: collapse;
                page-break-after: always;
            }}
            .vale-cell {{
                vertical-align: top;
                padding: 2px;
                page-break-inside: avoid;
                border: 1px solid #ccc; /* opcional para depuración */
            }}
            /* Estilos generales para el contenido del vale */
            table {{
                border-collapse: collapse;
                width: 100%;
                font-size: 7px;
            }}
            th, td {{
                font-size: 7px;
                padding: 1px;
                word-wrap: break-word;
            }}
            .first-td {{
                font-size: 8px;
                padding: 1px;
            }}
            .table-info-td {{
                font-size: 7px;
                padding: 0.8px;
            }}
            h1 {{
                font-size: 10px;
                margin: 0;
            }}
            img {{
                max-height: 25px;
                width: auto;
            }}
            /* Ajustar tablas internas para que no se desborden */
            .vale-cell table {{
                table-layout: fixed;
            }}
        </style>
    </head>
    <body>
        {''.join(pages)}
    </body>
    </html>
    """

    # ---- GENERAR PDF ----
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="vales_multiple.pdf"'

    def link_callback(uri, rel):
            result = finders.find(uri)
            if result:
                    if not isinstance(result, (list, tuple)):
                            result = [result]
                    result = list(os.path.realpath(path) for path in result)
                    path=result[0]
            else:
                    sUrl = settings.STATIC_URL       
                    sRoot = settings.STATIC_ROOT     
                    mUrl = settings.MEDIA_URL        
                    mRoot = settings.MEDIA_ROOT   

                    if uri.startswith(mUrl):
                            path = os.path.join(mRoot, uri.replace(mUrl, ""))
                    elif uri.startswith(sUrl):
                            path = os.path.join(sRoot, uri.replace(sUrl, ""))
                    else:
                            return uri

            # make sure that file exists
            if not os.path.isfile(path):
                    raise RuntimeError(
                            'media URI must start with %s or %s' % (sUrl, mUrl)
                    )
            return path

    pisa_status = pisa.CreatePDF(
        combined_html,
        dest=response,
        link_callback=link_callback
    )

    if pisa_status.err:
        return HttpResponse(f'Error al generar PDF: {pisa_status.err}')

    return response

# Para visualizar las imagenes en el pdf
def link_callback(uri, rel):
            result = finders.find(uri)
            if result:
                    if not isinstance(result, (list, tuple)):
                            result = [result]
                    result = list(os.path.realpath(path) for path in result)
                    path=result[0]
            else:
                    sUrl = settings.STATIC_URL       
                    sRoot = settings.STATIC_ROOT     
                    mUrl = settings.MEDIA_URL        
                    mRoot = settings.MEDIA_ROOT   

                    if uri.startswith(mUrl):
                            path = os.path.join(mRoot, uri.replace(mUrl, ""))
                    elif uri.startswith(sUrl):
                            path = os.path.join(sRoot, uri.replace(sUrl, ""))
                    else:
                            return uri

            # make sure that file exists
            if not os.path.isfile(path):
                    raise RuntimeError(
                            'media URI must start with %s or %s' % (sUrl, mUrl)
                    )
            return path