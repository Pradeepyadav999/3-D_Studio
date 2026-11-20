"""Size Chart Extraction Service for parsing OCR output into structured garment measurements."""
import re
from typing import Dict, Any, List, Optional, Tuple
from backend.models.schemas import SizeChartData, MeasurementValues

# Canonical size definitions
SIZE_VARIANTS = {
    "XS": ["XS", "X-S", "EXTRA SMALL"],
    "S": ["S", "SMALL"],
    "M": ["M", "MED", "MEDIUM"],
    "L": ["L", "LRG", "LARGE"],
    "XL": ["XL", "X-L", "EXTRA LARGE", "1XL"],
    "XXL": ["XXL", "2XL", "2-XL", "EXTRA EXTRA LARGE"],
    "3XL": ["3XL", "XXXL", "3-XL"]
}

# Measurement alias mappings
MEASUREMENT_ALIASES = {
    "chest": [
        "chest", "bust", "half chest", "1/2 chest", "chest width", "torso",
        "across chest", "pit to pit", "chest circumference", "half-chest"
    ],
    "shoulder": [
        "shoulder", "shoulders", "across shoulder", "shoulder width",
        "cross shoulder", "shoulder to shoulder"
    ],
    "length": [
        "length", "body length", "center back", "total length",
        "hsp to hem", "high point shoulder", "back length", "front length"
    ],
    "sleeve": [
        "sleeve", "sleeves", "sleeve length", "short sleeve",
        "sleeve from shoulder", "arm length"
    ],
    "waist": [
        "waist", "waist width", "1/2 waist", "waist circumference"
    ],
    "hem": [
        "hem", "bottom", "sweep", "bottom opening", "1/2 hem"
    ],
    "neck": [
        "neck", "collar", "neck opening", "neck circumference"
    ],
    "sleeve_opening": [
        "sleeve opening", "cuff", "bicep", "arm opening"
    ]
}

class ExtractionService:
    @classmethod
    def clean_number(cls, token_str: str) -> Optional[float]:
        """Cleans common OCR digit misrecognitions and converts to float."""
        text = token_str.strip().lower()
        # Remove common units attached to numbers
        text = re.sub(r'(cm|in|inch|inches|mm|")', '', text)
        # Common OCR fixes (letter O/o -> 0, l/I -> 1, s -> 5)
        replacements = {
            'o': '0',
            'l': '1',
            'i': '1',
            '|': '1',
        }
        for k, v in replacements.items():
            if re.match(r'^[0-9oli|.]+$', text):
                text = text.replace(k, v)
        try:
            val = float(text)
            return val
        except ValueError:
            # Check if there is a number embedded like "107.5"
            match = re.search(r'(\d+(?:\.\d+)?)', text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
            return None

    @classmethod
    def detect_unit(cls, raw_text: str) -> str:
        """Detects whether chart uses cm or inches."""
        text_lower = raw_text.lower()
        cm_count = len(re.findall(r'\b(cm|centimeter|centimetre|centimeters)\b', text_lower))
        inch_count = len(re.findall(r'\b(inch|inches|in|\"|in\.)\b', text_lower))
        if inch_count > cm_count and inch_count > 0:
            return "inch"
        return "cm"

    @classmethod
    def detect_measurement_type(cls, raw_text: str) -> Tuple[str, List[str]]:
        """
        Distinguishes garment measurements from body measurements.
        Returns: (measurement_type, warnings)
        """
        text_lower = raw_text.lower()
        warnings = []
        body_keywords = ["body measurement", "to fit chest", "body size", "measure your body", "actual body"]
        garment_keywords = ["garment measurement", "product measurement", "flat lay", "finished garment"]

        is_body = any(kw in text_lower for kw in body_keywords)
        is_garment = any(kw in text_lower for kw in garment_keywords)

        if is_body and not is_garment:
            warnings.append(
                "Warning: This chart appears to contain BODY measurements rather than finished garment measurements. "
                "Standard garment ease allowance should be considered."
            )
            return "body", warnings

        return "garment", warnings

    @classmethod
    def match_measurement_label(cls, text: str) -> Optional[str]:
        """Matches a string to a canonical measurement field."""
        cleaned = re.sub(r'[^a-z0-9/ ]', '', text.lower()).strip()
        for field, aliases in MEASUREMENT_ALIASES.items():
            for alias in aliases:
                if alias == cleaned or cleaned.startswith(alias) or alias in cleaned:
                    return field
        return None

    @classmethod
    def match_size_label(cls, text: str) -> Optional[str]:
        """Matches a string to a canonical garment size (S, M, L, XL, etc.)."""
        cleaned = re.sub(r'[^A-Z0-9-]', '', text.upper()).strip()
        for size_key, aliases in SIZE_VARIANTS.items():
            if cleaned in aliases:
                return size_key
        return None

    @classmethod
    def extract_from_raw_and_tokens(cls, chart_id: str, raw_text: str, tokens: List[Dict[str, Any]]) -> SizeChartData:
        """
        Primary extraction algorithm parsing OCR lines and spatial tokens into structured sizes.
        """
        unit = cls.detect_unit(raw_text)
        measurement_type, warnings = cls.detect_measurement_type(raw_text)

        # 1. Parse lines of text
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

        detected_sizes: List[str] = []
        size_col_indices: Dict[str, int] = {}
        row_data: Dict[str, List[Tuple[float, float]]] = {}  # field -> list of (val, conf)
        cell_confidences: Dict[str, Dict[str, float]] = {}

        # Look for header line with sizes (e.g. "Size S M L XL" or "Measurement S M L XL XXL")
        header_line_idx = -1
        for idx, line in enumerate(lines):
            line_upper = line.upper()
            found_sizes_in_line = []
            tokens_in_line = re.split(r'[\s|,|\t|;]+', line)
            for t in tokens_in_line:
                matched_size = cls.match_size_label(t)
                if matched_size and matched_size not in found_sizes_in_line:
                    found_sizes_in_line.append(matched_size)

            if len(found_sizes_in_line) >= 2:
                # High confidence header row found!
                header_line_idx = idx
                detected_sizes = found_sizes_in_line
                for s_i, sz in enumerate(detected_sizes):
                    size_col_indices[sz] = s_i
                break

        # Fallback if no clean header line found: search tokens by Y coordinate clustering
        if not detected_sizes and tokens:
            y_groups: Dict[int, List[Dict[str, Any]]] = {}
            for t in tokens:
                matched_sz = cls.match_size_label(t["text"])
                if matched_sz:
                    # Group by row approx +- 15px
                    placed = False
                    for y_key in y_groups:
                        if abs(y_key - t["y"]) < 20:
                            y_groups[y_key].append(t)
                            placed = True
                            break
                    if not placed:
                        y_groups[t["y"]] = [t]

            # Find the group with the most distinct sizes
            best_y_group = None
            max_distinct = 0
            for y_k, t_list in y_groups.items():
                distinct = set(cls.match_size_label(tk["text"]) for tk in t_list)
                if len(distinct) > max_distinct:
                    max_distinct = len(distinct)
                    best_y_group = sorted(t_list, key=lambda item: item["x"])

            if best_y_group and max_distinct >= 2:
                for tk in best_y_group:
                    sz = cls.match_size_label(tk["text"])
                    if sz and sz not in detected_sizes:
                        detected_sizes.append(sz)
                        size_col_indices[sz] = len(detected_sizes) - 1

        # If still no sizes detected, provide default standard sizes
        if not detected_sizes:
            detected_sizes = ["S", "M", "L", "XL"]
            warnings.append("Could not confidently identify size headers. Used standard [S, M, L, XL].")

        # Now extract rows: for each subsequent line after header
        for idx, line in enumerate(lines):
            if idx == header_line_idx:
                continue

            # Check if line starts with or contains a measurement label
            matched_field = None
            # Extract numbers in this line
            line_parts = re.split(r'[\s|,|\t|;]+', line)
            numbers_in_line = []
            words_in_line = []

            for part in line_parts:
                num = cls.clean_number(part)
                if num is not None:
                    numbers_in_line.append(num)
                else:
                    words_in_line.append(part)

            label_candidate = " ".join(words_in_line)
            matched_field = cls.match_measurement_label(label_candidate)

            if matched_field and numbers_in_line:
                if matched_field not in row_data:
                    row_data[matched_field] = []
                for n in numbers_in_line:
                    row_data[matched_field].append((n, 0.90))

        # Check if any half-chest measurements were found and adjust
        if "chest" in row_data:
            chest_values = [v[0] for v in row_data["chest"]]
            if chest_values and all(35.0 <= val <= 65.0 for val in chest_values):
                # These are half-chest values!
                warnings.append("Extracted chest values appear to be half-chest widths. Doubling to full circumference.")
                row_data["chest"] = [(val * 2.0, conf) for (val, conf) in row_data["chest"]]

        # Build structured sizes dictionary
        sizes_dict: Dict[str, MeasurementValues] = {}
        for sz_idx, size_key in enumerate(detected_sizes):
            cell_confidences[size_key] = {}

            # Get values for this column index, or fallback smoothly
            def get_val_for_field(field_name: str, default_val: float) -> float:
                if field_name in row_data and len(row_data[field_name]) > sz_idx:
                    val, conf = row_data[field_name][sz_idx]
                    cell_confidences[size_key][field_name] = conf
                    return val
                elif field_name in row_data and len(row_data[field_name]) > 0:
                    # Extrapolate or use last available
                    val, conf = row_data[field_name][-1]
                    cell_confidences[size_key][field_name] = 0.60
                    return val
                else:
                    cell_confidences[size_key][field_name] = 0.50
                    return default_val

            # Standard industry grading defaults if OCR missed certain fields
            # S: 96, M: 101, L: 107, XL: 112, XXL: 118
            size_offsets = {"XS": -5, "S": 0, "M": 5, "L": 11, "XL": 16, "XXL": 22, "3XL": 28, "4XL": 34}
            offset = size_offsets.get(size_key, 0)

            chest = get_val_for_field("chest", 96.0 + offset)
            shoulder = get_val_for_field("shoulder", 40.0 + offset * 0.4)
            length = get_val_for_field("length", 66.0 + offset * 0.4)
            sleeve = get_val_for_field("sleeve", 18.0 + offset * 0.15)

            # Optional fields
            waist = get_val_for_field("waist", None) if "waist" in row_data else None
            hem = get_val_for_field("hem", None) if "hem" in row_data else None
            neck = get_val_for_field("neck", None) if "neck" in row_data else None
            sleeve_opening = get_val_for_field("sleeve_opening", None) if "sleeve_opening" in row_data else None

            sizes_dict[size_key] = MeasurementValues(
                chest=chest,
                shoulder=shoulder,
                length=length,
                sleeve=sleeve,
                waist=waist,
                hem=hem,
                neck=neck,
                sleeve_opening=sleeve_opening
            )

        # Compute overall confidence
        all_confs = [c for sz_c in cell_confidences.values() for c in sz_c.values()]
        overall_conf = float(sum(all_confs) / len(all_confs)) if all_confs else 0.85

        return SizeChartData(
            chart_id=chart_id,
            unit=unit,
            measurement_type=measurement_type,
            confidence=round(overall_conf, 2),
            sizes=sizes_dict,
            raw_ocr_text=raw_text,
            cell_confidences=cell_confidences,
            warnings=warnings
        )
