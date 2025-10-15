# Publicar en GitHub Pages (guía rápida)

Esta guía te lleva de cero a publicado usando la carpeta `web/` como sitio estático.

## 1) Crea un repositorio en GitHub

- Inicia sesión en GitHub y crea un repo nuevo (p. ej. `florecer`).
- En tu equipo, asegúrate de tener Git configurado (nombre/email) y de inicializar el repositorio si aún no lo está.

## 2) Sube el código a GitHub

Desde la carpeta raíz del proyecto (la que contiene `web/`):

```powershell
# Inicializa (si aún no está)
git init
# Añade todo, incluyendo web/
git add .
# Commit inicial
git commit -m "Init web with rose renderer"
# Renombra tu rama local a main (si no lo está)
git branch -M main
# Conecta con el remoto (sustituye USUARIO y REPO)
git remote add origin https://github.com/USUARIO/REPO.git
# Sube a GitHub
git push -u origin main
```

## 3) Habilita GitHub Pages

- En GitHub, ve a Settings → Pages.
- En "Build and deployment":
  - Source: GitHub Actions.
- Guarda los cambios.

Este repositorio ya incluye un workflow en `.github/workflows/deploy-pages.yml` que publica el contenido de `web/`.

## 4) Publica

- Cada push a `main` disparará el workflow y publicará el sitio.
- Puedes dispararlo manualmente en la pestaña "Actions" → "Deploy to GitHub Pages" → "Run workflow".

Cuando termine, verás una URL similar a:

```
https://USUARIO.github.io/REPO/
```

Ahí se servirá `index.html` dentro de `web/` y los recursos de `web/resources/`.

## 5) Estructura necesaria

- `web/index.html`
- `web/styles.css`
- `web/main.js`
- `web/resources/rosas.json` (y otros JSON si quieres)
- `web/.nojekyll` (para evitar que Jekyll interfiera)

## 6) Problemas frecuentes

- Página en blanco o error cargando JSON:
  - Asegúrate de que `web/resources/rosas.json` está en el repo.
  - Revisa la consola del navegador (F12) para ver errores.
- 404 en Pages justo después de activar:
  - Espera 1–3 minutos a que termine el despliegue.
- Ruta del JSON:
  - En `main.js` usamos `./resources/rosas.json`, que funciona bien en Pages (sirve desde la misma carpeta `web/`).

## 7) ¿Subdominio personalizado?

- En Settings → Pages, añade tu custom domain y configura los registros DNS (CNAME) en tu proveedor.
- Crea un archivo `web/CNAME` con tu dominio para fijarlo en el sitio.
