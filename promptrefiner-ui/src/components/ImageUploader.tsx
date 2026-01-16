'use client';

import { useState, useRef, DragEvent, ChangeEvent } from 'react';

export interface UploadedImage {
    file: File;
    preview: string;
    base64: string;
}

interface ImageUploaderProps {
    images: UploadedImage[];
    onChange: (images: UploadedImage[]) => void;
    maxImages?: number;
    disabled?: boolean;
}

export function ImageUploader({
    images,
    onChange,
    maxImages = 3,
    disabled = false,
}: ImageUploaderProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const processFiles = async (files: FileList | File[]) => {
        const fileArray = Array.from(files);
        const validFiles = fileArray.filter(
            (file) => file.type.startsWith('image/') && file.size < 10 * 1024 * 1024 // 10MB limit
        );

        const remainingSlots = maxImages - images.length;
        const filesToProcess = validFiles.slice(0, remainingSlots);

        const newImages: UploadedImage[] = await Promise.all(
            filesToProcess.map(async (file) => {
                const preview = URL.createObjectURL(file);
                const base64 = await fileToBase64(file);
                return { file, preview, base64 };
            })
        );

        onChange([...images, ...newImages]);
    };

    const fileToBase64 = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const result = reader.result as string;
                // Remove data URL prefix to get pure base64
                const base64 = result.split(',')[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        if (!disabled) setIsDragOver(true);
    };

    const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragOver(false);
    };

    const handleDrop = (e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragOver(false);
        if (!disabled && e.dataTransfer.files.length > 0) {
            processFiles(e.dataTransfer.files);
        }
    };

    const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            processFiles(e.target.files);
        }
    };

    const handleRemove = (index: number) => {
        const newImages = [...images];
        URL.revokeObjectURL(newImages[index].preview);
        newImages.splice(index, 1);
        onChange(newImages);
    };

    const canAddMore = images.length < maxImages;

    return (
        <div className="space-y-3">
            <label className="text-sm font-medium text-soft">
                Reference Image(s) (optional)
            </label>

            {/* Preview existing images */}
            {images.length > 0 && (
                <div className="flex flex-wrap gap-3">
                    {images.map((img, index) => (
                        <div
                            key={index}
                            className="relative group rounded-xl overflow-hidden border border-[var(--surface-border)] shadow-md"
                        >
                            <img
                                src={img.preview}
                                alt={`Upload ${index + 1}`}
                                className="h-24 w-24 object-cover"
                            />
                            <button
                                type="button"
                                onClick={() => handleRemove(index)}
                                className="absolute top-1 right-1 h-6 w-6 flex items-center justify-center rounded-full bg-red-500/80 text-white text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-red-600"
                                aria-label="Remove image"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Drop zone */}
            {canAddMore && (
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => !disabled && fileInputRef.current?.click()}
                    className={`
            flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed p-6 cursor-pointer transition-all duration-300
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-cyan-400 hover:bg-cyan-500/5'}
            ${isDragOver ? 'border-cyan-400 bg-cyan-500/10 scale-[1.02]' : 'border-[var(--surface-border)]'}
          `}
                >
                    <svg
                        className="h-8 w-8 text-muted"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                    </svg>
                    <span className="text-sm text-muted">
                        {isDragOver ? 'Drop image here' : 'Drag & drop or click to upload'}
                    </span>
                    <span className="text-xs text-muted/60">
                        PNG, JPG, WebP up to 10MB • {images.length}/{maxImages} images
                    </span>
                </div>
            )}

            <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                multiple
                className="hidden"
                onChange={handleFileSelect}
                disabled={disabled}
            />
        </div>
    );
}
