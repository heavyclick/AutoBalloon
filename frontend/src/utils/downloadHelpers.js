/**
 * downloadHelpers.js
 * Utility functions for file downloads
 */

/**
 * Downloads a Blob as a file
 * @param {Blob} blob - The blob to download
 * @param {string} filename - The filename to save as
 */
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  a.remove();
}
