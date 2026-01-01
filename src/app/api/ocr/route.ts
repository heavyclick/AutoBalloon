/**
 * OCR API Route - Google Cloud Vision Integration
 *
 * This endpoint receives a base64 image and returns OCR text
 * Used for:
 * - Raster PDF fallback (when vector text < 5 strings)
 * - Manual balloon addition (local 100x100px crop)
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { image } = await request.json();

    if (!image) {
      return NextResponse.json({ error: 'No image provided' }, { status: 400 });
    }

    // Extract base64 data (remove data:image/png;base64, prefix)
    const base64Data = image.replace(/^data:image\/\w+;base64,/, '');

    // Call Google Cloud Vision API
    const visionApiKey = process.env.NEXT_PUBLIC_GOOGLE_VISION_API_KEY;

    if (!visionApiKey) {
      return NextResponse.json(
        { error: 'Google Vision API key not configured' },
        { status: 500 }
      );
    }

    const response = await fetch(
      `https://vision.googleapis.com/v1/images:annotate?key=${visionApiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requests: [
            {
              image: {
                content: base64Data,
              },
              features: [
                {
                  type: 'DOCUMENT_TEXT_DETECTION',
                  maxResults: 100,
                },
              ],
            },
          ],
        }),
      }
    );

    if (!response.ok) {
      throw new Error('Google Vision API request failed');
    }

    const data = await response.json();

    // Extract text annotations
    const textAnnotations = data.responses[0]?.textAnnotations || [];

    // Format response
    const extractedText = textAnnotations.map((annotation: any) => ({
      text: annotation.description,
      confidence: annotation.confidence || 1.0,
      boundingBox: annotation.boundingPoly?.vertices || [],
    }));

    return NextResponse.json({
      success: true,
      text: extractedText,
    });
  } catch (error) {
    console.error('OCR error:', error);
    return NextResponse.json(
      { success: false, error: 'OCR processing failed' },
      { status: 500 }
    );
  }
}
