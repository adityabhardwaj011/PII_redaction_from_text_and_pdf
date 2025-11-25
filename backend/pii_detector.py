import re
import spacy
import json
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from pathlib import Path

# Try to load Gemini - we need this for smart PII detection
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Load spaCy model for name detection
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


class GeminiValidator:
    def __init__(self, api_key: str):
        if not api_key or not api_key.strip():
            raise ValueError("GEMINI_API_KEY is required. Please set it in your .env file.")
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package is not installed. Run: pip install google-generativeai")
        
        self.api_key = api_key
        
        try:
            genai.configure(api_key=api_key)
            self.model = None
            
            # Try to find a working model - skip experimental ones (they have no free tier)
            try:
                print("Listing available Gemini models...")
                for model in genai.list_models():
                    if 'generateContent' in model.supported_generation_methods:
                        model_name = model.name.split('/')[-1]
                        
                        # Skip experimental models - they usually have no free quota
                        if any(x in model_name.lower() for x in ['exp', 'experimental', '2.5', '2.0', '3.0']):
                            print(f"Skipping experimental model: {model_name}")
                            continue
                        
                        try:
                            self.model = genai.GenerativeModel(model_name)
                            print(f"✓ Successfully using model: {model_name}")
                            break
                        except Exception as e:
                            print(f"✗ Failed to use {model_name}: {str(e)[:100]}")
                            continue
            except Exception as e:
                print(f"Failed to list models: {e}")
            
            # If listing didn't work, try common free-tier model names
            if not self.model:
                print("Trying fallback model names...")
                for name in ['gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']:
                    try:
                        self.model = genai.GenerativeModel(name)
                        print(f"✓ Using fallback model: {name}")
                        break
                    except Exception as e:
                        print(f"✗ {name} not available: {str(e)[:100]}")
                        continue
            
            if not self.model:
                raise ValueError("Could not find any available Gemini model. Please check your API key and model availability.")
            
            self.enabled = True
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini API: {e}. Please check your GEMINI_API_KEY.")
    
    def validate_pii(self, text: str, candidate: str, pii_type: str, context: str) -> Tuple[bool, str]:
        if not self.enabled:
            raise RuntimeError("Gemini validator is not properly initialized")
        
        try:
            prompt = f"""You are a PII (Personally Identifiable Information) detection expert.

Context: {context}

Question: Is "{candidate}" actually a {pii_type} that should be redacted?

Consider:
- Is it real PII or a false positive (e.g., example email, book title, field label)?
- Does it appear in a context that suggests it's not real PII (e.g., "email@example.com is just the name of a training module")?

Respond in JSON format:
{{
    "is_pii": true/false,
    "reasoning": "brief explanation"
}}"""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                is_pii = result.get("is_pii", True)
                reasoning = result.get("reasoning", "No reasoning provided")
                return is_pii, reasoning
            except json.JSONDecodeError:
                if "false" in result_text.lower() or "not pii" in result_text.lower():
                    return False, result_text
                return True, result_text
                
        except Exception as e:
            error_msg = str(e)
            # Handle quota exceeded errors
            if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                raise RuntimeError(
                    f"Gemini API quota exceeded. You've hit the free tier limit. "
                    f"Please wait a few minutes or upgrade your plan. Error: {error_msg}"
                )
            raise RuntimeError(f"Gemini validation failed: {e}. Please check your API key and network connection.")
    
    def discover_pii(self, text: str, existing_detections: Dict[str, List[Dict]]) -> List[Dict]:
        if not self.enabled:
            raise RuntimeError("Gemini validator is not properly initialized")
        
        try:
            existing_summary = []
            for pii_type, items in existing_detections.items():
                if items:
                    existing_summary.append(f"{pii_type}: {len(items)} found")
            
            prompt = f"""You are a PII (Personally Identifiable Information) detection expert.

Text to analyze:
{text[:2000]}

Already detected:
{', '.join(existing_summary) if existing_summary else 'None'}

Find any additional PII that might have been missed:
- Email addresses
- Phone numbers
- Names (first, last, or full names)
- Physical addresses
- Social Security Numbers
- Credit card numbers
- Usernames or account IDs
- Any other personally identifiable information

Respond in JSON format:
{{
    "new_detections": [
        {{
            "type": "email|phone|name|address|ssn|credit_card|username|other",
            "value": "the detected text",
            "start": character_position,
            "end": character_position,
            "confidence": "high|medium|low",
            "reasoning": "why this is PII"
        }}
    ]
}}"""
            
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result = json.loads(result_text)
                new_detections = result.get("new_detections", [])
                
                validated = []
                for det in new_detections:
                    value = det.get("value", "")
                    start = det.get("start", -1)
                    end = det.get("end", -1)
                    
                    if start == -1 or end == -1:
                        pos = text.find(value)
                        if pos != -1:
                            start = pos
                            end = pos + len(value)
                        else:
                            continue
                    
                    validated.append({
                        "type": det.get("type", "other"),
                        "value": value,
                        "start": start,
                        "end": end,
                        "confidence": det.get("confidence", "medium"),
                        "reasoning": det.get("reasoning", "")
                    })
                
                return validated
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            error_msg = str(e)
            # Handle quota exceeded errors
            if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                raise RuntimeError(
                    f"Gemini API quota exceeded. You've hit the free tier limit. "
                    f"Please wait a few minutes or upgrade your plan. Error: {error_msg}"
                )
            raise RuntimeError(f"Gemini discovery failed: {e}. Please check your API key and network connection.")
    
    def explain_redaction(self, text: str, detections: Dict[str, List[Dict]]) -> str:
        if not self.enabled:
            raise RuntimeError("Gemini validator is not properly initialized")
        
        try:
            summary = []
            for pii_type, items in detections.items():
                if items:
                    summary.append(f"{pii_type}: {len(items)} detected")
            
            prompt = f"""Summarize the PII redaction process for this document.

Detected PII:
{', '.join(summary) if summary else 'No PII detected'}

Provide a clear, concise explanation of:
1. What types of PII were found
2. Why they were redacted
3. Any notable patterns or edge cases handled

Keep it brief (2-3 sentences)."""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e)
            # Handle quota exceeded errors
            if "429" in error_msg or "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                raise RuntimeError(
                    f"Gemini API quota exceeded. You've hit the free tier limit. "
                    f"Please wait a few minutes or upgrade your plan. Error: {error_msg}"
                )
            raise RuntimeError(f"Gemini explanation failed: {e}. Please check your API key and network connection.")


class PIIDetector:
    def __init__(self, config_path: Optional[str] = None, gemini_api_key: str = None):
        self.config = self._load_config(config_path)
        
        if not gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required for PII detection. "
                "Please set it in your .env file. Get your free key from: https://makersuite.google.com/app/apikey"
            )
        self.gemini = GeminiValidator(gemini_api_key)
        # Regex patterns for finding different types of PII
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone numbers come in many formats
        self.phone_patterns = [
            re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),  # US format
            re.compile(r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),  # International
            re.compile(r'\d{3}-\d{3}-\d{4}'),  # XXX-XXX-XXXX
            re.compile(r'\(\d{3}\)\s?\d{3}-\d{4}'),
        ]
        
        self.ssn_pattern = re.compile(
            r'\b\d{3}-\d{2}-\d{4}\b|\b\d{3}\s\d{2}\s\d{4}\b'
        )
        
        self.credit_card_pattern = re.compile(
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        )
        
        self.address_patterns = [
            re.compile(r'\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)[\s,]+[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?', re.IGNORECASE),
            re.compile(r'\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)[\s,]+[A-Za-z\s]+,\s*[A-Z]{2}', re.IGNORECASE),
        ]
        
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        if config_path is None:
            config_path = Path(__file__).parent / "pii_config.json"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: Config file not found at {config_path}. Using default empty config.")
                return {}
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing config file {config_path}: {e}. Using default empty config.")
            return {}
        except Exception as e:
            print(f"Warning: Error loading config file {config_path}: {e}. Using default empty config.")
            return {}
    
    def detect_emails(self, text: str, settings: Dict) -> List[Dict]:
        """Detect email addresses"""
        if not settings.get("redact_emails", True):
            return []
        
        emails = []
        matches = self.email_pattern.finditer(text)
        
        for match in matches:
            emails.append({
                "type": "email",
                "value": match.group(),
                "start": match.start(),
                "end": match.end()
            })
        
        return emails
    
    def detect_phones(self, text: str, settings: Dict) -> List[Dict]:
        """Detect phone numbers"""
        if not settings.get("redact_phones", True):
            return []
        
        phones = []
        seen_positions = set()
        
        for pattern in self.phone_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                pos = (match.start(), match.end())
                if pos in seen_positions:
                    continue
                seen_positions.add(pos)
                
                phone = match.group()
                # Make sure it has at least 10 digits (valid phone number)
                if len(re.sub(r'\D', '', phone)) >= 10:
                    phones.append({
                        "type": "phone",
                        "value": phone,
                        "start": match.start(),
                        "end": match.end()
                    })
        
        return phones
    
    def detect_ssn(self, text: str, settings: Dict) -> List[Dict]:
        """Detect Social Security Numbers"""
        if not settings.get("redact_ssn", True):
            return []
        
        ssns = []
        matches = self.ssn_pattern.finditer(text)
        
        for match in matches:
            ssn = match.group()
            ssns.append({
                "type": "ssn",
                "value": ssn,
                "start": match.start(),
                "end": match.end()
            })
        
        return ssns
    
    def detect_credit_cards(self, text: str, settings: Dict) -> List[Dict]:
        """Detect credit card numbers"""
        if not settings.get("redact_credit_cards", True):
            return []
        
        credit_cards = []
        matches = self.credit_card_pattern.finditer(text)
        
        for match in matches:
            card = match.group()
            # Credit cards should have exactly 16 digits
            digits = re.sub(r'\D', '', card)
            if len(digits) == 16:
                credit_cards.append({
                    "type": "credit_card",
                    "value": card,
                    "start": match.start(),
                    "end": match.end()
                })
        
        return credit_cards
    
    def detect_addresses(self, text: str, settings: Dict) -> List[Dict]:
        """Detect physical addresses"""
        if not settings.get("redact_addresses", True):
            return []
        
        addresses = []
        seen_positions = set()
        
        for pattern in self.address_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                pos = (match.start(), match.end())
                if pos in seen_positions:
                    continue
                seen_positions.add(pos)
                
                address = match.group()
                addresses.append({
                    "type": "address",
                    "value": address,
                    "start": match.start(),
                    "end": match.end()
                })
        
        return addresses
    
    def detect_names(self, text: str, settings: Dict) -> List[Dict]:
        if not settings.get("redact_names", True) or nlp is None:
            return []
        
        # Use spaCy to find person names in the text
        names = []
        doc = nlp(text)
        
        seen_positions = set()
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Skip very short names (probably false positives)
                if len(ent.text.strip()) < 2:
                    continue
                
                pos = (ent.start_char, ent.end_char)
                if pos in seen_positions:
                    continue
                seen_positions.add(pos)
                
                name_text = ent.text.strip()
                start = ent.start_char
                end = ent.end_char
                
                names.append({
                    "type": "name",
                    "value": name_text,
                    "start": start,
                    "end": end
                })
        
        # Merge names that are close together (like "Emily" and "Johnson")
        merged_names = []
        names_sorted = sorted(names, key=lambda x: x["start"])
        
        i = 0
        while i < len(names_sorted):
            current = names_sorted[i]
            j = i + 1
            while j < len(names_sorted):
                next_name = names_sorted[j]
                # If names are within 5 chars, they're probably first + last name
                if next_name["start"] - current["end"] <= 5:
                    current = {
                        "type": "name",
                        "value": f"{current['value']} {next_name['value']}",
                        "start": current["start"],
                        "end": next_name["end"]
                    }
                    j += 1
                else:
                    break
            merged_names.append(current)
            i = j
        
        return merged_names
    
    def detect_usernames(self, text: str, settings: Dict) -> List[Dict]:
        if not settings.get("redact_names", True):
            return []
        
        username_pattern = re.compile(
            r'\b(?:username|user|login|account)\s*(?:is|:)\s+([a-z0-9_]{3,20})\b', 
            re.IGNORECASE
        )
        
        usernames = []
        seen_positions = set()
        
        matches = username_pattern.finditer(text)
        for match in matches:
            username = match.group(1)
            pos = (match.start(1), match.end(1))
            
            if pos in seen_positions:
                continue
            seen_positions.add(pos)
            
            # Don't treat email usernames as separate usernames
            email_context = text[max(0, match.start() - 10):min(len(text), match.end() + 10)]
            if '@' in email_context:
                continue
            
            usernames.append({
                "type": "name",
                "value": username,
                "start": pos[0],
                "end": pos[1]
            })
        
        return usernames
    
    def detect_all(self, text: str, settings: Dict) -> Tuple[Dict[str, List[Dict]], str]:
        # Step 1: Find names and usernames using regex and spaCy
        names = self.detect_names(text, settings)
        usernames = self.detect_usernames(text, settings)
        
        # Combine usernames with names, avoiding duplicates
        name_positions = {(n["start"], n["end"]) for n in names}
        for username in usernames:
            pos = (username["start"], username["end"])
            if pos not in name_positions:
                overlap = False
                for name in names:
                    if not (username["end"] <= name["start"] or username["start"] >= name["end"]):
                        overlap = True
                        break
                if not overlap:
                    names.append(username)
        
        # Step 2: Find all other PII types using regex
        results = {
            "emails": self.detect_emails(text, settings),
            "phones": self.detect_phones(text, settings),
            "names": names,
            "addresses": self.detect_addresses(text, settings),
            "ssn": self.detect_ssn(text, settings),
            "credit_cards": self.detect_credit_cards(text, settings)
        }
        
        # Step 3: Validate everything with Gemini (filters false positives)
        validated_results = {}
        for pii_type, items in results.items():
            validated_items = []
            
            # Special handling for names - keep full names together
            if pii_type == "names":
                name_groups = []
                items_sorted = sorted(items, key=lambda x: x["start"])
                
                for item in items_sorted:
                    added_to_group = False
                    for group in name_groups:
                        for group_item in group:
                            if abs(item["start"] - group_item["end"]) <= 5 or abs(item["end"] - group_item["start"]) <= 5:
                                group.append(item)
                                added_to_group = True
                                break
                        if added_to_group:
                            break
                    
                    if not added_to_group:
                        name_groups.append([item])
                
                for group in name_groups:
                    if len(group) > 1:
                        merged_name = {
                            "type": "name",
                            "value": " ".join(sorted([n["value"] for n in group], key=lambda x: group[0]["start"])),
                            "start": min(n["start"] for n in group),
                            "end": max(n["end"] for n in group)
                        }
                        start = max(0, merged_name["start"] - 100)
                        end = min(len(text), merged_name["end"] + 100)
                        context = text[start:end]
                        
                        is_valid, reasoning = self.gemini.validate_pii(
                            text, merged_name["value"], pii_type, context
                        )
                        if is_valid:
                            merged_name["gemini_reasoning"] = reasoning
                            validated_items.append(merged_name)
                        else:
                            # Even if Gemini says no, keep full names together
                            merged_name["gemini_reasoning"] = f"Full name context: {reasoning}"
                            validated_items.append(merged_name)
                    else:
                        item = group[0]
                        start = max(0, item["start"] - 100)
                        end = min(len(text), item["end"] + 100)
                        context = text[start:end]
                        
                        is_valid, reasoning = self.gemini.validate_pii(
                            text, item["value"], pii_type, context
                        )
                        if is_valid:
                            item["gemini_reasoning"] = reasoning
                            validated_items.append(item)
                        else:
                            # If single name rejected but near another name, keep it anyway
                            for validated in validated_items:
                                if abs(item["start"] - validated["end"]) <= 5 or abs(item["end"] - validated["start"]) <= 5:
                                    item["gemini_reasoning"] = f"Part of full name context: {reasoning}"
                                    validated_items.append(item)
                                    break
            else:
                for item in items:
                    start = max(0, item["start"] - 100)
                    end = min(len(text), item["end"] + 100)
                    context = text[start:end]
                    
                    is_valid, reasoning = self.gemini.validate_pii(
                        text, item["value"], pii_type, context
                    )
                    if is_valid:
                        item["gemini_reasoning"] = reasoning
                        validated_items.append(item)
            
            validated_results[pii_type] = validated_items
        
        # Step 4: Ask Gemini to find anything we might have missed
        new_detections = self.gemini.discover_pii(text, validated_results)
        
        # Add new discoveries to our results
        for new_det in new_detections:
            det_type = new_det.get("type", "other")
            type_mapping = {
                "email": "emails",
                "phone": "phones",
                "name": "names",
                "address": "addresses",
                "ssn": "ssn",
                "credit_card": "credit_cards",
                "username": "names"
            }
            mapped_type = type_mapping.get(det_type, "names")
            
            if mapped_type not in validated_results:
                validated_results[mapped_type] = []
            
            # Don't add duplicates
            is_duplicate = False
            for existing in validated_results[mapped_type]:
                if (existing["start"] == new_det["start"] and 
                    existing["end"] == new_det["end"]):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                validated_results[mapped_type].append({
                    "type": mapped_type.rstrip('s'),
                    "value": new_det["value"],
                    "start": new_det["start"],
                    "end": new_det["end"],
                    "gemini_discovered": True,
                    "confidence": new_det.get("confidence", "medium"),
                    "reasoning": new_det.get("reasoning", "")
                })
        
        results = validated_results
        explanation = self.gemini.explain_redaction(text, results)
        
        return results, explanation
    
    def get_redaction_label(self, pii_type: str, index: int, settings: Dict) -> str:
        style = settings.get("redaction_style", "labels")
        
        if style == "black_boxes":
            return "█" * 8
        elif style == "custom":
            custom = settings.get("custom_label", "[REDACTED]")
            return custom
        else:
            type_labels = {
                "email": "EMAIL",
                "phone": "PHONE",
                "name": "NAME",
                "address": "ADDRESS",
                "ssn": "SSN",
                "credit_card": "CARD"
            }
            label = type_labels.get(pii_type, "REDACTED")
            return f"[{label}_{index + 1}]"
    
    def redact_text(self, text: str, detections: Dict[str, List[Dict]], settings: Dict) -> str:
        # Collect all detections and assign redaction labels
        all_detections = []
        type_counts = defaultdict(int)
        
        for pii_type, items in detections.items():
            for item in items:
                if settings.get(f"redact_{pii_type}", True):
                    type_counts[pii_type] += 1
                    index = type_counts[pii_type] - 1
                    all_detections.append({
                        **item,
                        "redaction_label": self.get_redaction_label(pii_type, index, settings)
                    })
        
        if not all_detections:
            return text
        
        # Sort by size (largest first) so we handle bigger matches first
        all_detections.sort(key=lambda x: (-(x["end"] - x["start"]), x["start"]))
        
        # Remove overlapping detections - keep the largest one
        filtered_detections = []
        for det in all_detections:
            overlaps = False
            for kept in filtered_detections:
                if not (det["end"] <= kept["start"] or det["start"] >= kept["end"]):
                    overlaps = True
                    break
            if not overlaps:
                filtered_detections.append(det)
        
        # Sort by position (reverse order) so we redact from end to start
        # This way positions don't shift as we replace text
        filtered_detections.sort(key=lambda x: x["start"], reverse=True)
        
        # Replace detected PII with redaction labels
        redacted_text = text
        for detection in filtered_detections:
            start = detection["start"]
            end = detection["end"]
            if 0 <= start < end <= len(text):
                original_text_at_pos = text[start:end]
                detected_value = detection.get("value", "")
                
                # Make sure we're replacing the right thing
                if original_text_at_pos == detected_value or detected_value in original_text_at_pos:
                    redacted_text = redacted_text[:start] + detection["redaction_label"] + redacted_text[end:]
        
        return redacted_text

