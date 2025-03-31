import { Biomarker } from '../types/biomarker';
import { parseISO, compareDesc } from 'date-fns';

export type ProcessedFavoriteData = {
  name: string;
  latestValue: string | null;
  latestUnit: string | null;
  latestDate: Date | null;
  latestReferenceRange: string | null;
  previousValue: string | null;
  previousUnit: string | null;
  previousDate: Date | null;
  status: 'Normal' | 'Abnormal' | 'Borderline' | 'Unknown'; // Added Borderline possibility
  trend: 'Up' | 'Down' | 'Stable' | 'Unknown';
  history: { date: Date; value: number }[]; // Added for sparkline
  category?: string; // Added category for icon mapping
};

/**
 * Parses the reference range string to extract min and max values.
 * Handles various formats like "X - Y", "< X", "> Y".
 * @param rangeStr - The reference range string.
 * @returns An object with min and max values (can be null).
 */
const parseReferenceRange = (
  rangeStr: string | null
): { min: number | null; max: number | null } => {
  if (!rangeStr) return { min: null, max: null };

  rangeStr = rangeStr.replace(/,/g, ''); // Remove commas for parsing

  // Handle ranges like "X - Y" or "X to Y"
  const rangeMatch = rangeStr.match(/([\d.]+)\s*[-–—to]+\s*([\d.]+)/);
  if (rangeMatch) {
    return { min: parseFloat(rangeMatch[1]), max: parseFloat(rangeMatch[2]) };
  }

  // Handle "< X" or "Less than X"
  const lessThanMatch = rangeStr.match(/(?:<|Less than)\s*([\d.]+)/i);
  if (lessThanMatch) {
    return { min: null, max: parseFloat(lessThanMatch[1]) };
  }

  // Handle "> X" or "Greater than X"
  const greaterThanMatch = rangeStr.match(/(?:>|Greater than)\s*([\d.]+)/i);
  if (greaterThanMatch) {
    return { min: parseFloat(greaterThanMatch[1]), max: null };
  }

  // Handle "Up to X"
  const upToMatch = rangeStr.match(/Up to\s*([\d.]+)/i);
   if (upToMatch) {
     return { min: null, max: parseFloat(upToMatch[1]) };
   }

  // Handle single value ranges (less common, treat as exact target?)
  const singleValueMatch = rangeStr.match(/^([\d.]+)$/);
  if (singleValueMatch) {
      // Cannot determine range from single value, treat as unknown
      // Alternatively, could treat as min=max=value, but that's ambiguous
      return { min: null, max: null };
  }


  // If no pattern matches, return nulls
  console.warn(`Could not parse reference range: "${rangeStr}"`);
  return { min: null, max: null };
};

/**
 * Determines the status (Normal/Abnormal) based on value and reference range.
 * @param value - The biomarker value as a number.
 * @param rangeStr - The reference range string.
 * @returns 'Normal', 'Abnormal', or 'Unknown'.
 */
const getBiomarkerStatus = (
  value: number | null,
  rangeStr: string | null
): 'Normal' | 'Abnormal' | 'Borderline' | 'Unknown' => { // Added Borderline possibility
  // TODO: Implement Borderline logic if applicable (e.g., based on thresholds near range limits)
  // For now, keeping it simple: Normal or Abnormal
  if (value === null || rangeStr === null) return 'Unknown';

  // Value is already a number, no need to parse
  if (isNaN(value)) return 'Unknown';

  const { min, max } = parseReferenceRange(rangeStr);

  if (min !== null && max !== null) {
    return value >= min && value <= max ? 'Normal' : 'Abnormal';
  } else if (min !== null) {
    return value >= min ? 'Normal' : 'Abnormal';
  } else if (max !== null) {
    return value <= max ? 'Normal' : 'Abnormal';
  }

  return 'Unknown'; // Cannot determine status if range is unclear
};

/**
 * Determines the trend based on latest and previous numeric values.
 * @param latestValue - The latest biomarker value as a number.
 * @param previousValue - The previous biomarker value as a number.
 * @returns 'Up', 'Down', 'Stable', or 'Unknown'.
 */
const getBiomarkerTrend = (
  latestValue: number | null,
  previousValue: number | null
): 'Up' | 'Down' | 'Stable' | 'Unknown' => {
  if (latestValue === null || previousValue === null) return 'Unknown';

  // Values are already numbers
  if (isNaN(latestValue) || isNaN(previousValue)) return 'Unknown';

  // Add a small tolerance for floating point comparisons
  const tolerance = 0.001;
  if (Math.abs(latestValue - previousValue) < tolerance) {
    return 'Stable';
  } else if (latestValue > previousValue) {
    return 'Up';
  } else {
    return 'Down';
  }
};

/**
 * Processes a list of all biomarkers for a profile to extract data for favorites.
 * Finds the latest and previous values for each favorite biomarker.
 * Calculates status and trend.
 *
 * @param allBiomarkers - Array of all Biomarker objects for the profile.
 * @param favoriteNames - Array of biomarker names marked as favorite.
 * @returns An array of ProcessedFavoriteData objects.
 */
export const processBiomarkersForFavorites = (
  allBiomarkers: Biomarker[],
  favoriteNames: string[]
): ProcessedFavoriteData[] => {
  const processedFavorites: ProcessedFavoriteData[] = [];
  const biomarkersByName: { [key: string]: Biomarker[] } = {};

  // --- Synonym Mapping ---
  const synonymMap: { [key: string]: string } = {
    '25-Hydroxyvitamin D': 'Vitamin D',
    // Add other synonyms here if needed
    // e.g., 'LDL': 'LDL Cholesterol' 
  };

  const normalizeName = (name: string): string => {
    return synonymMap[name] || name; // Return canonical name if synonym found, else original
  };

  // Group biomarkers by NORMALIZED name
  allBiomarkers.forEach((bm) => {
    const normalized = normalizeName(bm.name);
    if (!biomarkersByName[normalized]) {
      biomarkersByName[normalized] = [];
    }
    // Push the original biomarker object, but group under the normalized key
    biomarkersByName[normalized].push(bm); 
  });

  // Process each favorite name (use normalized name for lookup)
  favoriteNames.forEach((favName) => {
    // Ensure we look up using the potentially normalized favorite name
    // Although, ideally, favorites stored in localStorage should also be normalized.
    // For now, assume favName might be a synonym and normalize it for lookup.
    const normalizedFavName = normalizeName(favName); 
    const history = biomarkersByName[normalizedFavName] || [];

    // Sort by date descending (most recent first)
    const sortedHistory = history
      .map(bm => ({ ...bm, dateObject: bm.date ? parseISO(bm.date) : null }))
      .filter(bm => bm.dateObject !== null)
      .sort((a, b) => compareDesc(a.dateObject!, b.dateObject!));

    const latest = sortedHistory[0] || null;
    const previous = sortedHistory[1] || null;

    // Use correct property name 'referenceRange' and pass numbers directly
    const status = getBiomarkerStatus(latest?.value ?? null, latest?.referenceRange ?? null);
    const trend = getBiomarkerTrend(latest?.value ?? null, previous?.value ?? null);

    processedFavorites.push({
      name: normalizedFavName, // Use the normalized/canonical name for the output object
      // Convert numbers to strings for the output type
      latestValue: latest?.value?.toString() ?? null,
      latestUnit: latest?.unit ?? null,
      latestDate: latest?.dateObject ?? null,
      latestReferenceRange: latest?.referenceRange ?? null, // Use correct property name
      previousValue: previous?.value?.toString() ?? null,
      previousUnit: previous?.unit ?? null,
      previousDate: previous?.dateObject ?? null,
      status: status, // Status calculation might need update for Borderline
      trend: trend,
      category: latest?.category, // Add the category from the latest record
      // Map sorted history to the required format for the sparkline
      history: sortedHistory.map(bm => ({
        date: bm.dateObject!, // Already filtered non-null dates
        value: bm.value!,     // Assuming value is always present if date is
      })).sort((a, b) => a.date.getTime() - b.date.getTime()), // Ensure history is sorted chronologically for sparkline
    });
  });

  return processedFavorites;
};
