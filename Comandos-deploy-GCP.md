## Paso 0: Vinculación
gcloud init

## Paso 1: Creación del repositorio
gcloud artifacts repositories create repositorio-backend-langchain-inmobiliaria --repository-format docker --project datapath-ai17-naty-garcia --location us-central1

## Paso 2: Crear la imagen de mi APLICACION y subir al repositorio
gcloud builds submit --config=cloudbuild.yaml --project datapath-ai17-kevin-inofuente

## Paso 3: Comando para despliegue o ejecución de la imagen en el repositorio
gcloud run services replace service.yaml --region us-central1 --project datapath-ai17-kevin-inofuente

## Paso 4: OPCIONAL, Dar permisos de acceso a mi APLICACION. ESTO SE EJECUTA UNA SOLA VEZ
gcloud run services set-iam-policy servicio-backend-inmobiliaria-kevin-inofuente gcr-service-policy.yaml --region us-central1 --project datapath-ai17-kevin-inofuente

---

## Paso previo recomendado: probar la imagen en local antes de gastar un build en la nube
# Si el contenedor no arranca acá, tampoco va a arrancar en Cloud Run.
docker build -f Dockerfile.prod -t agente-inmobiliaria:local .
docker run --rm -p 4000:4000 agente-inmobiliaria:local
curl http://localhost:4000/health

## Paso 5: Obtener la URL del servicio desplegado
gcloud run services describe servicio-backend-inmobiliaria-kevin-inofuente --region us-central1 --project datapath-ai17-kevin-inofuente --format 'value(status.url)'

## Paso 6: Verificar el servicio en la nube
# Reemplaza <URL> por la del Paso 5. El webhook de Chatwoot apunta a <URL>/webhook
curl <URL>/health

## Ver los logs si algo falla al arrancar
gcloud run services logs read servicio-backend-inmobiliaria-kevin-inofuente --region us-central1 --project datapath-ai17-kevin-inofuente --limit 50
