FROM nginx:alpine

# Remove default Nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy only the required HTML pages
COPY index.html /usr/share/nginx/html/
#COPY index2.html /usr/share/nginx/html/
#COPY index3.html /usr/share/nginx/html/

# Expose HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
