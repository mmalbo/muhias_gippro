from .models import Vale_Movimiento_Almacen, Transportista, Movimiento_EE, Movimiento_Ins, Movimiento_MP
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.contrib.staticfiles import finders
import os

def export_vale(request, id_movimiento):
   data = {}
   #data['date'] = 
   #Diccionario de vale
   current_vale = {}        
   movimiento = Vale_Movimiento_Almacen.objects.filter(consecutivo=id_movimiento)[0]

   inventarios = Movimiento_MP.objects.filter(vale=movimiento.id)
   data['tipop'] = 'MP'
   if not inventarios:
      inventarios = Movimiento_EE.objects.filter(vale_e=movimiento.id)
      data['tipop'] = 'ENV'
   if not inventarios:
      inventarios = Movimiento_Ins.objects.filter(vale_e=movimiento.id)
      data['tipop'] = 'INS'
   if not inventarios:
      return HttpResponse('No se registraron movimientos de inventario con ese id')   
   else:
      data['consecutivo'] = movimiento.consecutivo
      data['almacen'] = movimiento.almacen
      data['fecha'] = movimiento.fecha_movimiento
      data['suministrador'] = movimiento.suministrador
      data['orden'] = movimiento.orden_No
      data['lote'] = movimiento.lote_No
      data['tipoi'] = movimiento.tipo
      if movimiento.transportista:
         data['nombre_transportista'] = movimiento.transportista.nombre
         data['ci_transportista'] = movimiento.transportista.cI
         data['cargo_transportista'] = movimiento.transportista.cargo
      else:
         data['nombre_transportista'] = ''
         data['ci_transportista'] = ''
         data['cargo_transportista'] = ''
      data['chapa'] = movimiento.suministrador
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