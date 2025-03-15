"""
Biomarker Dictionary Module

This module provides a dictionary of common biomarkers found in lab reports,
including their various naming conventions and unit standards.
"""
from typing import Dict, List, Any, Tuple

# Dictionary of biomarkers with their alternate names and unit standardization info
# Format:
# "standard_name": {
#     "alternate_names": [list of alternate names/spellings that could appear in reports],
#     "standard_unit": preferred unit for storage and display,
#     "unit_conversions": {
#         "unit1": conversion factor to standard unit,
#         "unit2": conversion factor to standard unit,
#     }
# }

BIOMARKER_DICT: Dict[str, Dict[str, Any]] = {
    # Blood Glucose Markers
    "Glucose": {
        "alternate_names": [
            "GLUCOSE", "Blood Glucose", "Fasting Glucose", "Fasting Blood Sugar", 
            "FBS", "GLU", "Blood Sugar", "FASTING BLOOD SUGAR(GLUCOSE)"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "mmol/L": 18.0182,  # 1 mmol/L = 18.0182 mg/dL
            "mmol/l": 18.0182,
        },
        "category": "Metabolic",
        "reference_ranges": {
            "adult": {"low": 70, "high": 99, "unit": "mg/dL", "context": "fasting"},
            "pre_diabetic": {"low": 100, "high": 125, "unit": "mg/dL", "context": "fasting"},
            "diabetic": {"low": 126, "high": None, "unit": "mg/dL", "context": "fasting"}
        }
    },
    
    "HbA1c": {
        "alternate_names": [
            "GLYCOSYLATED HEMOGLOBIN", "Glycosylated Hemoglobin", "HBA1C", "A1c", 
            "Glycated Hemoglobin", "Hemoglobin A1c", "HEMOGLOBIN A1C"
        ],
        "standard_unit": "%",
        "unit_conversions": {
            "%": 1.0,
            "mmol/mol": 0.09148,  # IFCC to DCCT/NGSP conversion
        },
        "category": "Metabolic",
        "reference_ranges": {
            "normal": {"low": None, "high": 5.6, "unit": "%"},
            "pre_diabetic": {"low": 5.7, "high": 6.4, "unit": "%"},
            "diabetic": {"low": 6.5, "high": None, "unit": "%"}
        }
    },
    
    # Lipid Panel
    "Total Cholesterol": {
        "alternate_names": [
            "CHOLESTEROL", "Cholesterol", "T-Chol", "TOTAL CHOLESTEROL", "CHOLESTEROL-TOTAL",
            "T. Cholesterol", "Serum Cholesterol"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "mmol/L": 38.67,  # 1 mmol/L = 38.67 mg/dL
            "mmol/l": 38.67,
        },
        "category": "Lipid",
        "reference_ranges": {
            "desirable": {"low": None, "high": 200, "unit": "mg/dL"},
            "borderline_high": {"low": 200, "high": 239, "unit": "mg/dL"},
            "high": {"low": 240, "high": None, "unit": "mg/dL"}
        }
    },
    
    "HDL": {
        "alternate_names": [
            "HDL CHOLESTEROL", "HDL-C", "HDL-CHOLESTEROL", "High Density Lipoprotein", 
            "Good Cholesterol", "HDL Cholesterol"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "mmol/L": 38.67,  # 1 mmol/L = 38.67 mg/dL
            "mmol/l": 38.67,
        },
        "category": "Lipid",
        "reference_ranges": {
            "low": {"low": None, "high": 40, "unit": "mg/dL", "gender": "male"},
            "low": {"low": None, "high": 50, "unit": "mg/dL", "gender": "female"},
            "optimal": {"low": 60, "high": None, "unit": "mg/dL"}
        }
    },
    
    "LDL": {
        "alternate_names": [
            "LDL CHOLESTEROL", "LDL-C", "LDL-CHOLESTEROL", "Low Density Lipoprotein",
            "Bad Cholesterol", "LDL Cholesterol"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "mmol/L": 38.67,  # 1 mmol/L = 38.67 mg/dL
            "mmol/l": 38.67,
        },
        "category": "Lipid",
        "reference_ranges": {
            "optimal": {"low": None, "high": 100, "unit": "mg/dL"},
            "near_optimal": {"low": 100, "high": 129, "unit": "mg/dL"},
            "borderline_high": {"low": 130, "high": 159, "unit": "mg/dL"},
            "high": {"low": 160, "high": 189, "unit": "mg/dL"},
            "very_high": {"low": 190, "high": None, "unit": "mg/dL"}
        }
    },
    
    "Triglycerides": {
        "alternate_names": [
            "TRIGLYCERIDES", "TG", "Trigs", "Triglyceride", "TRIGLYCERIDE"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "mmol/L": 88.57,  # 1 mmol/L = 88.57 mg/dL
            "mmol/l": 88.57,
        },
        "category": "Lipid",
        "reference_ranges": {
            "normal": {"low": None, "high": 150, "unit": "mg/dL"},
            "borderline_high": {"low": 150, "high": 199, "unit": "mg/dL"},
            "high": {"low": 200, "high": 499, "unit": "mg/dL"},
            "very_high": {"low": 500, "high": None, "unit": "mg/dL"}
        }
    },
    
    # Complete Blood Count
    "Hemoglobin": {
        "alternate_names": [
            "HGB", "Hgb", "HB", "HEMOGLOBIN", "Hb", "HEMOGLOBIN(HB)"
        ],
        "standard_unit": "g/dL",
        "unit_conversions": {
            "g/dL": 1.0,
            "g/dl": 1.0,
            "g/L": 0.1,  # 1 g/L = 0.1 g/dL
            "g/l": 0.1,
        },
        "category": "Hematology",
        "reference_ranges": {
            "male": {"low": 13.0, "high": 17.0, "unit": "g/dL"},
            "female": {"low": 12.0, "high": 15.5, "unit": "g/dL"}
        }
    },
    
    "RBC Count": {
        "alternate_names": [
            "RBC", "Red Blood Cell Count", "Erythrocytes", "Red Cell Count", 
            "REDBLOODCELL(RBC)COUNT", "RED BLOOD CELL COUNT"
        ],
        "standard_unit": "mil/µL",
        "unit_conversions": {
            "mil/µL": 1.0,
            "mil/uL": 1.0,
            "10^6/µL": 1.0,
            "10^6/uL": 1.0,
            "x10^12/L": 1.0,
            "10^12/L": 1.0
        },
        "category": "Hematology",
        "reference_ranges": {
            "male": {"low": 4.5, "high": 5.9, "unit": "mil/µL"},
            "female": {"low": 4.0, "high": 5.2, "unit": "mil/µL"}
        }
    },
    
    "WBC Count": {
        "alternate_names": [
            "WBC", "White Blood Cell Count", "Leukocytes", "White Cell Count", 
            "WHITEBLOODCELL(WBC)COUNT", "WHITE BLOOD CELL COUNT"
        ],
        "standard_unit": "thou/µL",
        "unit_conversions": {
            "thou/µL": 1.0,
            "thou/uL": 1.0,
            "10^3/µL": 1.0,
            "10^3/uL": 1.0,
            "x10^9/L": 1.0,
            "10^9/L": 1.0,
            "K/uL": 1.0,
            "K/µL": 1.0
        },
        "category": "Hematology",
        "reference_ranges": {
            "adult": {"low": 4.0, "high": 11.0, "unit": "thou/µL"}
        }
    },
    
    "Platelets": {
        "alternate_names": [
            "PLT", "Platelet Count", "Thrombocytes", "PLATELETCOUNT", "PLATELET COUNT"
        ],
        "standard_unit": "thou/µL",
        "unit_conversions": {
            "thou/µL": 1.0,
            "thou/uL": 1.0,
            "10^3/µL": 1.0,
            "10^3/uL": 1.0,
            "x10^9/L": 1.0,
            "10^9/L": 1.0,
            "K/uL": 1.0,
            "K/µL": 1.0
        },
        "category": "Hematology",
        "reference_ranges": {
            "adult": {"low": 150, "high": 450, "unit": "thou/µL"}
        }
    },
    
    # Thyroid Panel
    "TSH": {
        "alternate_names": [
            "Thyroid Stimulating Hormone", "Thyrotropin", "TSH - ULTRASENS", 
            "Thyroid-Stimulating Hormone", "THYROID STIMULATING HORMONE"
        ],
        "standard_unit": "µIU/mL",
        "unit_conversions": {
            "µIU/mL": 1.0,
            "uIU/ml": 1.0,
            "uIU/mL": 1.0,
            "µIU/ml": 1.0,
            "mIU/L": 1.0
        },
        "category": "Endocrine",
        "reference_ranges": {
            "adult": {"low": 0.4, "high": 4.0, "unit": "µIU/mL"}
        }
    },
    
    "T3": {
        "alternate_names": [
            "Triiodothyronine", "Total T3", "TOTAL TRIIODOTHYRONINE (T3)", 
            "T3 TOTAL", "Total Triiodothyronine"
        ],
        "standard_unit": "ng/dL",
        "unit_conversions": {
            "ng/dL": 1.0,
            "ng/dl": 1.0,
            "nmol/L": 65.1,  # 1 nmol/L = 65.1 ng/dL
            "nmol/l": 65.1,
        },
        "category": "Endocrine",
        "reference_ranges": {
            "adult": {"low": 80, "high": 200, "unit": "ng/dL"}
        }
    },
    
    "T4": {
        "alternate_names": [
            "Thyroxine", "Total T4", "TOTAL THYROXINE (T4)", 
            "T4 TOTAL", "Total Thyroxine"
        ],
        "standard_unit": "µg/dL",
        "unit_conversions": {
            "µg/dL": 1.0,
            "ug/dl": 1.0,
            "ug/dL": 1.0,
            "µg/dl": 1.0,
            "nmol/L": 12.87,  # 1 nmol/L = 12.87 µg/dL
            "nmol/l": 12.87,
        },
        "category": "Endocrine",
        "reference_ranges": {
            "adult": {"low": 5.0, "high": 12.0, "unit": "µg/dL"}
        }
    },
    
    # Vitamins
    "Vitamin D": {
        "alternate_names": [
            "25-OH Vitamin D", "25-Hydroxyvitamin D", "25-OH VITAMIN D (TOTAL)", 
            "Vitamin D3", "25-OH Vit D", "25(OH)D"
        ],
        "standard_unit": "ng/mL",
        "unit_conversions": {
            "ng/mL": 1.0,
            "ng/ml": 1.0,
            "nmol/L": 0.4,  # 1 nmol/L = 0.4 ng/mL
            "nmol/l": 0.4,
        },
        "category": "Vitamin",
        "reference_ranges": {
            "deficiency": {"low": None, "high": 20, "unit": "ng/mL"},
            "insufficiency": {"low": 20, "high": 30, "unit": "ng/mL"},
            "sufficiency": {"low": 30, "high": 100, "unit": "ng/mL"},
            "toxicity": {"low": 100, "high": None, "unit": "ng/mL"}
        }
    },
    
    "Vitamin B12": {
        "alternate_names": [
            "VITAMIN B-12", "Cobalamin", "B12", 
            "VITAMIN B12", "Vit B12"
        ],
        "standard_unit": "pg/mL",
        "unit_conversions": {
            "pg/mL": 1.0,
            "pg/ml": 1.0,
            "pmol/L": 0.738,  # 1 pmol/L = 0.738 pg/mL
            "pmol/l": 0.738,
        },
        "category": "Vitamin",
        "reference_ranges": {
            "adult": {"low": 200, "high": 900, "unit": "pg/mL"}
        }
    },
    
    # Liver Function Tests
    "ALT": {
        "alternate_names": [
            "Alanine Aminotransferase", "SGPT", "ALANINE TRANSAMINASE",
            "Alanine Transaminase", "SGPT-ALANINE AMINOTRANSFERASE"
        ],
        "standard_unit": "U/L",
        "unit_conversions": {
            "U/L": 1.0,
            "IU/L": 1.0,
            "U/l": 1.0,
            "IU/l": 1.0
        },
        "category": "Liver",
        "reference_ranges": {
            "male": {"low": None, "high": 41, "unit": "U/L"},
            "female": {"low": None, "high": 33, "unit": "U/L"}
        }
    },
    
    "AST": {
        "alternate_names": [
            "Aspartate Aminotransferase", "SGOT", "ASPARTATE TRANSAMINASE",
            "Aspartate Transaminase", "SGOT-ASPARTATE AMINOTRANSFERASE"
        ],
        "standard_unit": "U/L",
        "unit_conversions": {
            "U/L": 1.0,
            "IU/L": 1.0,
            "U/l": 1.0,
            "IU/l": 1.0
        },
        "category": "Liver",
        "reference_ranges": {
            "male": {"low": None, "high": 40, "unit": "U/L"},
            "female": {"low": None, "high": 32, "unit": "U/L"}
        }
    },
    
    # Kidney Function Tests
    "Creatinine": {
        "alternate_names": [
            "CREATININE", "Serum Creatinine", "CREATININE-SERUM"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "µmol/L": 0.0113,  # 1 µmol/L = 0.0113 mg/dL
            "umol/L": 0.0113,
            "µmol/l": 0.0113,
            "umol/l": 0.0113
        },
        "category": "Kidney",
        "reference_ranges": {
            "male": {"low": 0.7, "high": 1.3, "unit": "mg/dL"},
            "female": {"low": 0.6, "high": 1.1, "unit": "mg/dL"}
        }
    },
    
    "BUN": {
        "alternate_names": [
            "Blood Urea Nitrogen", "Urea Nitrogen", "UREA", "Urea",
            "BLOOD UREA NITROGEN"
        ],
        "standard_unit": "mg/dL",
        "unit_conversions": {
            "mg/dL": 1.0,
            "mg/dl": 1.0,
            "mmol/L": 2.8,  # 1 mmol/L = 2.8 mg/dL (for urea)
            "mmol/l": 2.8
        },
        "category": "Kidney",
        "reference_ranges": {
            "adult": {"low": 7, "high": 20, "unit": "mg/dL"}
        }
    },
    
    # Electrolytes
    "Sodium": {
        "alternate_names": [
            "Na", "SODIUM", "Serum Sodium", "SODIUM-SERUM"
        ],
        "standard_unit": "mmol/L",
        "unit_conversions": {
            "mmol/L": 1.0,
            "mmol/l": 1.0,
            "mEq/L": 1.0,
            "mEq/l": 1.0
        },
        "category": "Electrolyte",
        "reference_ranges": {
            "adult": {"low": 135, "high": 145, "unit": "mmol/L"}
        }
    },
    
    "Potassium": {
        "alternate_names": [
            "K", "POTASSIUM", "Serum Potassium", "POTASSIUM-SERUM"
        ],
        "standard_unit": "mmol/L",
        "unit_conversions": {
            "mmol/L": 1.0,
            "mmol/l": 1.0,
            "mEq/L": 1.0,
            "mEq/l": 1.0
        },
        "category": "Electrolyte",
        "reference_ranges": {
            "adult": {"low": 3.5, "high": 5.0, "unit": "mmol/L"}
        }
    },
    
    "Chloride": {
        "alternate_names": [
            "Cl", "CHLORIDE", "Serum Chloride", "CHLORIDE-SERUM"
        ],
        "standard_unit": "mmol/L",
        "unit_conversions": {
            "mmol/L": 1.0,
            "mmol/l": 1.0,
            "mEq/L": 1.0,
            "mEq/l": 1.0
        },
        "category": "Electrolyte",
        "reference_ranges": {
            "adult": {"low": 98, "high": 107, "unit": "mmol/L"}
        }
    }
}

def get_standardized_biomarker_name(name: str) -> str:
    """
    Returns the standardized biomarker name if found in dictionary.
    
    Args:
        name: The biomarker name as found in the lab report
        
    Returns:
        str: Standardized biomarker name if found, original name otherwise
    """
    name = name.strip()
    
    # Direct match with a standard name
    if name in BIOMARKER_DICT:
        return name
    
    # Check all alternate names
    for standard_name, info in BIOMARKER_DICT.items():
        if name.upper() in [alt.upper() for alt in info["alternate_names"]]:
            return standard_name
    
    # No match found
    return name

def convert_to_standard_unit(value: float, current_unit: str, biomarker_name: str) -> Tuple[float, str]:
    """
    Converts a biomarker value to its standard unit.
    
    Args:
        value: The numeric value to convert
        current_unit: The current unit of the value
        biomarker_name: The standardized biomarker name
    
    Returns:
        Tuple[float, str]: Converted value and standard unit
    """
    standardized_name = get_standardized_biomarker_name(biomarker_name)
    
    # If biomarker not in dictionary, return original value and unit
    if standardized_name not in BIOMARKER_DICT:
        return value, current_unit
    
    biomarker_info = BIOMARKER_DICT[standardized_name]
    standard_unit = biomarker_info["standard_unit"]
    
    # If current unit is already the standard unit, no conversion needed
    if current_unit.strip().lower() == standard_unit.strip().lower():
        return value, standard_unit
    
    # If conversion factor exists, convert value
    if current_unit in biomarker_info["unit_conversions"]:
        converted_value = value * biomarker_info["unit_conversions"][current_unit]
        return converted_value, standard_unit
    
    # Check for case-insensitive unit match
    for unit, factor in biomarker_info["unit_conversions"].items():
        if unit.lower() == current_unit.lower():
            converted_value = value * factor
            return converted_value, standard_unit
            
    # No conversion factor found
    return value, current_unit

def get_biomarker_category(biomarker_name: str) -> str:
    """
    Returns the category of a biomarker.
    
    Args:
        biomarker_name: The standardized biomarker name
        
    Returns:
        str: Category of the biomarker or "Other" if not found
    """
    standardized_name = get_standardized_biomarker_name(biomarker_name)
    
    if standardized_name in BIOMARKER_DICT:
        return BIOMARKER_DICT[standardized_name].get("category", "Other")
    
    return "Other"

def get_reference_range(biomarker_name: str, gender: str = None, context: str = None) -> dict:
    """
    Returns the reference range for a biomarker.
    
    Args:
        biomarker_name: The standardized biomarker name
        gender: Optional gender for gender-specific ranges
        context: Optional context (e.g., "fasting" for glucose)
        
    Returns:
        dict: Reference range with low and high values, or empty dict if not found
    """
    standardized_name = get_standardized_biomarker_name(biomarker_name)
    
    if standardized_name not in BIOMARKER_DICT:
        return {}
    
    biomarker_info = BIOMARKER_DICT[standardized_name]
    if "reference_ranges" not in biomarker_info:
        return {}
    
    ranges = biomarker_info["reference_ranges"]
    
    # Check for gender-specific ranges if gender is provided
    if gender:
        gender = gender.lower()
        if gender in ranges:
            return ranges[gender]
    
    # Check for context-specific ranges if context is provided
    if context:
        context = context.lower()
        for key, range_info in ranges.items():
            if isinstance(range_info, dict) and range_info.get("context") == context:
                return range_info
    
    # Return adult or normal range as default
    if "adult" in ranges:
        return ranges["adult"]
    if "normal" in ranges:
        return ranges["normal"]
    
    # Return the first range found if no specific match
    for key, range_info in ranges.items():
        if isinstance(range_info, dict) and "low" in range_info and "high" in range_info:
            return range_info
            
    return {} 