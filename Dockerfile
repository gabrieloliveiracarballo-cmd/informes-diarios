# Usar una imagen de servidor web Nginx súper ligera
FROM nginx:stable-alpine

# Copiar todos los archivos de nuestro repositorio al directorio público del servidor web
COPY . /usr/share/nginx/html

# Exponer el puerto 80 para que se pueda acceder desde fuera
EXPOSE 80

# El comando para arrancar el servidor web (ya viene por defecto, pero así es explícito)
CMD ["nginx", "-g", "daemon off;"]