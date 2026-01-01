/**
 * Gemini API Route - Semantic Dimension Structuring
 *
 * Layer C: The Intelligence Layer
 *
 * Takes raw text strings (e.g., "2X Ø.125 +0.005/-0.002") and returns:
 * {
 *   quantity: 2,
 *   nominal: 0.125,
 *   plus_tol: 0.005,
 *   minus_tol: -0.002,
 *   units: "inch",
 *   type: "diameter",
 *   subtype: "Hole"
 * }
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { text } = await request.json();

    if (!text) {
      return NextResponse.json({ error: 'No text provided' }, { status: 400 });
    }

    const geminiApiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;

    if (!geminiApiKey) {
      return NextResponse.json(
        { error: 'Gemini API key not configured' },
        { status: 500 }
      );
    }

    // Construct the structured prompt
    const prompt = `You are an expert in engineering drawings and manufacturing specifications.

Parse the following dimension text into structured JSON:

Input: "${text}"

Output must be valid JSON with this exact schema:
{
  "nominal": number or null,
  "plus_tolerance": number or null,
  "minus_tolerance": number or null,
  "units": "in" | "mm" | "deg" | null,
  "tolerance_type": "bilateral" | "limit" | "fit" | "basic" | null,
  "subtype": "Linear" | "Diameter" | "Radius" | "Angle" | "Thread" | "GD&T" | "Note" | null,
  "is_gdt": boolean,
  "gdt_symbol": string or null,
  "fit_class": string or null,
  "thread_spec": string or null,
  "full_specification": string
}

Rules:
- If text contains Ø, set subtype to "Diameter"
- If text contains R, set subtype to "Radius"
- If text contains thread callout (e.g., "1/2-13 UNC"), set subtype to "Thread" and extract thread_spec
- If text contains GD&T symbols (⊥, ⌭, ⊕, etc.), set is_gdt to true
- If tolerance is ±X, set bilateral tolerance
- If tolerance is +X/-Y, set limit tolerance
- If text contains fit class (e.g., "H7/g6"), extract fit_class
- minus_tolerance should be negative (e.g., -0.002)

Return ONLY the JSON object, no additional text.`;

    // Call Gemini API
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiApiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  text: prompt,
                },
              ],
            },
          ],
          generationConfig: {
            temperature: 0.1,
            maxOutputTokens: 1024,
          },
        }),
      }
    );

    if (!response.ok) {
      throw new Error('Gemini API request failed');
    }

    const data = await response.json();

    // Extract the generated text
    const generatedText =
      data.candidates[0]?.content?.parts[0]?.text || '';

    // Parse the JSON response
    // Gemini sometimes wraps JSON in markdown code blocks, so we need to clean it
    const jsonMatch = generatedText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('Failed to extract JSON from Gemini response');
    }

    const parsed = JSON.parse(jsonMatch[0]);

    return NextResponse.json({
      success: true,
      parsed,
    });
  } catch (error) {
    console.error('Gemini error:', error);
    return NextResponse.json(
      { success: false, error: 'Gemini processing failed' },
      { status: 500 }
    );
  }
}
