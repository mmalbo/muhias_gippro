from .models import Vale_Movimiento_Almacen, Transportista, Movimiento_EE, Movimiento_Ins, Movimiento_MP
from inventario.models import Inv_Mat_Prima
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.contrib.staticfiles import finders
import os

def export_vale(request, id_movimiento):
   data = {}
   print(id_movimiento)
   #data['date'] = 
   #Diccionario de vale
   current_vale = {}        
   vale = Vale_Movimiento_Almacen.objects.filter(consecutivo=id_movimiento)[0]
   print(vale.tipo)
   inventarios = Movimiento_MP.objects.filter(vale=vale.id) #vale.movimientos.all()
   print(inventarios)
   if inventarios:
      tipo = 'materias primas'
   else:
      inventarios = vale.movimientos_e.all()
      if inventarios:
         tipo = 'envase o embalaje'
      else:
         inventarios = vale.movimientos_prod.all()
         if inventarios:
            tipo = 'productos'
         else:
            inventarios = vale.movimientos_i.all()
            if inventarios:
               tipo = 'insumos'
            else:
               inventarios = vale.mp_produccion.all()
               if inventarios:
                  tipo = 'Solicitud'
   data['tipop'] = tipo
   if not inventarios:
      return HttpResponse('No se registraron movimientos de inventario con ese id')   
   else:
      data['consecutivo'] = vale.consecutivo
      if tipo == 'Solicitud':
         data['almacen'] = vale.mp_produccion.first().almacen
      else:
         data['almacen'] = vale.almacen
      data['fecha'] = vale.fecha_movimiento
      data['suministrador'] = vale.suministrador
      data['origen'] = vale.origen
      data['destino'] = vale.destino 
      data['orden'] = vale.orden_No
      data['lote'] = vale.lote_No
      data['tipoi'] = vale.tipo.upper()
      if vale.transportista:
         data['nombre_transportista'] = vale.transportista
         data['ci_transportista'] = vale.transportista_cI
      else:
         data['nombre_transportista'] = ''
         data['ci_transportista'] = ''
         data['cargo_transportista'] = ''
      data['chapa'] = vale.chapa
      template_src = 'movimientos/vale.html'
      template = get_template(template_src)
      context = {'data': data, 'inventarios': inventarios, 'request': request}
      response = HttpResponse(content_type='application/pdf')
      response['Content-Disposition'] = 'attachment; filename="factura.pdf"'
      html = template.render(context)
      # create a pdf
      pisa_status = pisa.CreatePDF(
         html, dest=response, link_callback=link_callback)
      # if error then show some funny view
      if pisa_status.err:
         return HttpResponse('We had some errors <pre>' + html + '</pre>')
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