/**
 * Client-Side Math Engine
 * Uses decimal.js for precision arithmetic
 *
 * Prevents floating-point errors:
 * - 0.1 + 0.2 !== 0.3 (JavaScript bug)
 * - Decimal.js ensures: 0.1 + 0.2 === 0.3
 */

import Decimal from 'decimal.js';
import type { ParsedDimension } from '@/store/useAppStore';

/**
 * Calculate upper and lower limits from nominal and tolerances
 */
export function calculateLimits(
  nominal: number,
  plus_tol: number | null,
  minus_tol: number | null
): { upper_limit: number; lower_limit: number } {
  const nominalD = new Decimal(nominal);

  if (plus_tol !== null && minus_tol !== null) {
    const upperLimit = nominalD.plus(new Decimal(plus_tol));
    const lowerLimit = nominalD.plus(new Decimal(minus_tol)); // minus_tol is typically negative

    return {
      upper_limit: upperLimit.toNumber(),
      lower_limit: lowerLimit.toNumber(),
    };
  }

  // If no tolerances, limits = nominal
  return {
    upper_limit: nominal,
    lower_limit: nominal,
  };
}

/**
 * Automatic Tolerance (Block Logic)
 * Based on trailing decimal places
 */
export function getBlockTolerance(nominalStr: string): {
  plus_tolerance: number;
  minus_tolerance: number;
} {
  const decimalPlaces = getDecimalPlaces(nominalStr);

  // Standard block tolerances
  const blockTolerances: Record<number, number> = {
    0: 0.030, // .X
    1: 0.030, // .X
    2: 0.010, // .XX
    3: 0.005, // .XXX
    4: 0.0005, // .XXXX
  };

  const tolerance = blockTolerances[decimalPlaces] || 0.010;

  return {
    plus_tolerance: tolerance,
    minus_tolerance: -tolerance,
  };
}

/**
 * Get number of decimal places in a string
 */
function getDecimalPlaces(str: string): number {
  const match = str.match(/\.(\d+)/);
  return match ? match[1].length : 0;
}

/**
 * Auto-calculate all derived fields for a dimension
 */
export function calculateDerivedFields(
  nominal: number | null,
  plus_tol: number | null,
  minus_tol: number | null,
  rawValue: string
): Partial<ParsedDimension> {
  if (nominal === null) {
    return {};
  }

  // Apply block tolerance if no tolerances specified
  let finalPlusTol = plus_tol;
  let finalMinusTol = minus_tol;

  if (plus_tol === null || minus_tol === null) {
    const blockTol = getBlockTolerance(rawValue);
    finalPlusTol = blockTol.plus_tolerance;
    finalMinusTol = blockTol.minus_tolerance;
  }

  // Calculate limits
  const limits = calculateLimits(nominal, finalPlusTol, finalMinusTol);

  return {
    plus_tolerance: finalPlusTol,
    minus_tolerance: finalMinusTol,
    upper_limit: limits.upper_limit,
    lower_limit: limits.lower_limit,
  };
}

/**
 * Validate if an actual measurement is within limits
 */
export function isWithinLimits(
  actual: number,
  lower_limit: number,
  upper_limit: number
): boolean {
  const actualD = new Decimal(actual);
  const lowerD = new Decimal(lower_limit);
  const upperD = new Decimal(upper_limit);

  return actualD.greaterThanOrEqualTo(lowerD) && actualD.lessThanOrEqualTo(upperD);
}

/**
 * Calculate deviation from nominal
 */
export function calculateDeviation(actual: number, nominal: number): number {
  const actualD = new Decimal(actual);
  const nominalD = new Decimal(nominal);

  return actualD.minus(nominalD).toNumber();
}
