/** Utilidades de carga de logo tenant — resize seguro en cliente. */

export const LOGO_ALLOWED_TYPES = ["image/png", "image/jpeg", "image/svg+xml", "image/webp"] as const;
export const LOGO_MAX_INPUT_BYTES = 2_500_000;
export const LOGO_MAX_OUTPUT_BYTES = 400_000;
export const LOGO_MAX_DIMENSION = 512;

export type LogoProcessResult = {
  dataUrl: string;
  originalBytes: number;
  outputBytes: number;
  optimized: boolean;
};

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("No se pudo leer el archivo."));
    reader.readAsDataURL(file);
  });
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("No se pudo interpretar la imagen."));
    img.src = src;
  });
}

async function rasterize(
  img: HTMLImageElement,
  mime: "image/png" | "image/jpeg" | "image/webp",
  maxDim: number,
  quality: number,
): Promise<string> {
  const scale = Math.min(1, maxDim / Math.max(img.width, img.height, 1));
  const w = Math.max(1, Math.round(img.width * scale));
  const h = Math.max(1, Math.round(img.height * scale));
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas no disponible.");
  ctx.drawImage(img, 0, 0, w, h);
  return canvas.toDataURL(mime, quality);
}

/** Procesa logo: valida, optimiza raster si supera límite o dimensiones. */
export async function processLogoFile(file: File): Promise<LogoProcessResult> {
  if (!LOGO_ALLOWED_TYPES.includes(file.type as (typeof LOGO_ALLOWED_TYPES)[number])) {
    throw new Error("Formato no permitido. Use PNG, JPG, SVG o WebP.");
  }
  if (file.size > LOGO_MAX_INPUT_BYTES) {
    throw new Error(`El archivo supera ${Math.round(LOGO_MAX_INPUT_BYTES / 1_000_000)} MB.`);
  }

  const dataUrl = await readFileAsDataUrl(file);
  const originalBytes = file.size;

  if (file.type === "image/svg+xml") {
    if (dataUrl.length > LOGO_MAX_OUTPUT_BYTES * 1.4) {
      throw new Error("SVG demasiado grande. Use una versión optimizada o PNG.");
    }
    return { dataUrl, originalBytes, outputBytes: dataUrl.length, optimized: false };
  }

  const img = await loadImage(dataUrl);
  const needsResize =
    img.width > LOGO_MAX_DIMENSION ||
    img.height > LOGO_MAX_DIMENSION ||
    dataUrl.length > LOGO_MAX_OUTPUT_BYTES;

  if (!needsResize) {
    return { dataUrl, originalBytes, outputBytes: dataUrl.length, optimized: false };
  }

  const mime: "image/png" | "image/jpeg" | "image/webp" =
    file.type === "image/webp" ? "image/webp" : file.type === "image/jpeg" ? "image/jpeg" : "image/png";

  let quality = 0.92;
  let out = await rasterize(img, mime, LOGO_MAX_DIMENSION, quality);
  while (out.length > LOGO_MAX_OUTPUT_BYTES && quality > 0.5) {
    quality -= 0.08;
    out = await rasterize(img, mime, LOGO_MAX_DIMENSION, quality);
  }
  if (out.length > LOGO_MAX_OUTPUT_BYTES) {
    throw new Error("No se pudo optimizar el logo dentro del límite. Pruebe una imagen más pequeña.");
  }
  return { dataUrl: out, originalBytes, outputBytes: out.length, optimized: true };
}
