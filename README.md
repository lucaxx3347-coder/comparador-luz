# Comparador de luz con actualización diaria

Qué hace, sin coste:
- **Cada noche** una tarea automática de GitHub descarga el precio del PVPC (tarifa regulada) de Red Eléctrica y lo guarda en un histórico.
- **Comprueba** que los precios que tienes de cada compañía siguen apareciendo en las páginas que usas como fuente. **No los cambia solos**: si algo no coincide, la tarjeta de esa compañía muestra «⚠ Revisar precio».
- La app (`index.html`) lee `data/data.json` y calcula tu factura con tu consumo.

## Puesta en marcha (unos 15 minutos)

1. Crea una cuenta gratuita en github.com y un repositorio **público** llamado `comparador-luz`.
2. Sube **todo el contenido de esta carpeta** al repositorio. Ojo: la carpeta `.github` es oculta; si al arrastrar no se sube, crea en GitHub el archivo `.github/workflows/actualizar.yml` y pega su contenido.
3. En el repositorio: **Settings → Pages → Build and deployment → Deploy from a branch → main / (root) → Save**.
4. En **Settings → Actions → General → Workflow permissions**, marca **Read and write permissions** y guarda.
5. Ve a la pestaña **Actions → Actualizar datos → Run workflow** para lanzar la primera actualización sin esperar a la noche.
6. Tu app estará en `https://TU-USUARIO.github.io/comparador-luz/`. En el móvil, ábrela y elige «Añadir a pantalla de inicio».

## Cómo mantener los precios de las compañías

Los precios están en `data/companies.json` (uno por compañía, con la fecha de verificación). Cuando una tarjeta muestre «⚠ Revisar precio», mira la web de la compañía, corrige los números en ese archivo y cambia `verificado`. El campo `comprobar` indica qué página y qué cifras se vigilan.

## Cosas que debes saber

- Las comprobaciones leen páginas de comparadores y de compañías. Revisa sus condiciones de uso; el script hace **una sola consulta al día por página** y se identifica con un nombre propio. Si una página bloquea las consultas o carga los precios con JavaScript, aparecerá «Revisar precio» aunque el precio no haya cambiado: en ese caso cambia la página fuente en `comprobar`.
- El primer día verás qué páginas se pueden comprobar y cuáles no. Es normal ajustar algunas.
- El histórico inicial del PVPC (del 8 al 17 de noviembre) viene de Selectra; el día 18 y los siguientes vienen de la API de Red Eléctrica.
- Los precios de las compañías siguen siendo orientativos. Confirma siempre en la web oficial antes de contratar.
- Pruebas: `python -m unittest discover -s tests` (se ejecutan también cada noche).
