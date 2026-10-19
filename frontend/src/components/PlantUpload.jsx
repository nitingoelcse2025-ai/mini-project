import React, { useState, useRef } from 'react';
import { Camera, Trash2, AlertTriangle, ArrowRight } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const MAX_SIZE_MB = 5;

/**
 * Downscales an image client-side to a maximum of 1600px on its longest side.
 * Keeps canvas rendering at JPEG quality 0.85.
 */
const downscaleImage = (file, maxDimension = 1600, quality = 0.85) => {
  return new Promise((resolve) => {
    if (!file || !file.type.startsWith('image/')) {
      return resolve(file);
    }

    const reader = new FileReader();
    reader.onerror = () => resolve(file);
    reader.onload = (e) => {
      const img = new Image();
      img.onerror = () => resolve(file);
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        // If already within bounds, return original
        if (width <= maxDimension && height <= maxDimension) {
          return resolve(file);
        }

        if (width > height) {
          if (width > maxDimension) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          }
        } else {
          if (height > maxDimension) {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return resolve(file);

        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (!blob) return resolve(file);
            const baseName = file.name.replace(/\.[^/.]+$/, '');
            const resizedFile = new File([blob], `${baseName}.jpg`, {
              type: 'image/jpeg',
              lastModified: Date.now(),
            });
            resolve(resizedFile);
          },
          'image/jpeg',
          quality
        );
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
};

const PlantUpload = ({ onDiagnose, loading }) => {
  const { t } = useLanguage();
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [cropHint, setCropHint] = useState('');
  const [fileError, setFileError] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    validateAndSetFile(file);
  };

  const validateAndSetFile = (file) => {
    setFileError('');
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setFileError(t('plant.invalid_image_type'));
      return;
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setFileError(t('plant.size_limit_error'));
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setFileError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setFileError(t('plant.photo_required'));
      return;
    }

    setIsProcessing(true);
    try {
      // Downscale image to max 1600px on the longest side with 0.85 JPEG quality
      const processedFile = await downscaleImage(selectedFile, 1600, 0.85);
      onDiagnose({ file: processedFile, crop: cropHint.trim() });
    } catch (err) {
      console.warn('Downscaling failed, falling back to original file:', err);
      onDiagnose({ file: selectedFile, crop: cropHint.trim() });
    } finally {
      setIsProcessing(false);
    }
  };

  const isBusy = loading || isProcessing;

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-3xl p-6 sm:p-8 border border-emerald-100 shadow-sm space-y-6">
      {/* Upload / Camera Box */}
      <div>
        <label className="block text-base sm:text-lg font-extrabold text-stone-900 mb-2">
          {t('plant.upload_instruction')}
        </label>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileChange}
          className="hidden"
          id="plant-photo-input"
        />

        {!previewUrl ? (
          <label
            htmlFor="plant-photo-input"
            className="border-3 border-dashed border-emerald-200 hover:border-emerald-500 bg-emerald-50/50 hover:bg-emerald-50 transition-all rounded-3xl p-8 sm:p-12 flex flex-col items-center justify-center text-center cursor-pointer group"
          >
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-emerald-100 group-hover:bg-emerald-200 text-emerald-800 flex items-center justify-center mb-4 transition-transform group-hover:scale-105 shadow-sm">
              <Camera className="w-8 h-8 sm:w-10 sm:h-10" />
            </div>
            <span className="font-extrabold text-lg sm:text-xl text-emerald-950 mb-1">
              {t('plant.upload_button')}
            </span>
            <p className="text-stone-500 text-sm font-semibold">
              {t('plant.supported_types')}
            </p>
          </label>
        ) : (
          <div className="relative bg-stone-900/5 rounded-3xl p-3 border border-stone-200 flex flex-col items-center">
            <img
              src={previewUrl}
              alt="Plant leaf preview"
              className="max-h-72 w-full object-contain rounded-2xl shadow-sm"
            />
            <div className="flex items-center gap-3 mt-3 w-full justify-between px-2">
              <span className="text-sm font-bold text-stone-700 truncate max-w-[200px]">
                📷 {selectedFile?.name}
              </span>
              <button
                type="button"
                onClick={handleClear}
                disabled={isBusy}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-800 font-bold text-sm rounded-xl transition-colors cursor-pointer disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                <span>{t('plant.change_photo')}</span>
              </button>
            </div>
          </div>
        )}

        {fileError && (
          <p className="text-red-600 text-sm font-bold mt-2 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4" />
            <span>{fileError}</span>
          </p>
        )}
      </div>

      {/* Optional Crop Name */}
      <div>
        <label className="block text-base sm:text-lg font-extrabold text-stone-900 mb-2">
          {t('plant.crop_optional')}
        </label>
        <input
          type="text"
          value={cropHint}
          onChange={(e) => setCropHint(e.target.value)}
          placeholder={t('plant.crop_placeholder')}
          disabled={isBusy}
          className="w-full text-base sm:text-lg bg-stone-50 border-2 border-stone-200 focus:border-emerald-600 focus:bg-white rounded-2xl p-3.5 outline-none transition-all"
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isBusy || !selectedFile}
        className="w-full py-4 px-6 rounded-2xl font-extrabold text-lg sm:text-xl text-white bg-emerald-600 hover:bg-emerald-700 active:scale-[0.98] transition-all shadow-lg shadow-emerald-200 flex items-center justify-center gap-3 disabled:opacity-50 cursor-pointer"
      >
        <span>
          {isProcessing
            ? t('plant.compressing')
            : loading
            ? t('plant.analyzing')
            : t('plant.analyze_btn')}
        </span>
        {!isBusy && <ArrowRight className="w-6 h-6" />}
      </button>
    </form>
  );
};

export default PlantUpload;
