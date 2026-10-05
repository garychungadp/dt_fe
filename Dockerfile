# Frontend Nginx Container for Angular 20
FROM nginx:alpine

# Note: Misconfigurations intentionally present for Trivy security scan demonstration:
# 1. Missing USER statement (runs as root - DS-0002)
# 2. Missing HEALTHCHECK (DS-0026)

COPY dist/dt-fe/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
