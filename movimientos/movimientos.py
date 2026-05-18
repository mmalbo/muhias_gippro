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
      tipo.apppend('SolicitudMPP')
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
   print(tipo)
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
      template_src = 'movimientos/vale.html'
      template = get_template(template_src)
      context = {'data': data, 'inventarios_mp': inventarios_mp, 'inventarios_prod': inventarios_prod,
                 'inventarios_prod_prod': inventarios_prod_prod,'inventarios_mp_prod': inventarios_mp_prod, 
                 'inventarios_env': inventarios_env, 'inventarios_ins': inventarios_ins, 
                 'inventarios_env_env': inventarios_env_env, 'request': request}
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