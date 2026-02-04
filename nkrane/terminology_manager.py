# nkrane_gt/terminology_manager.py
import os
import csv
import pickle
import re
import spacy
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import pkg_resources

# Load spaCy model for English
try:
    nlp = spacy.load("en_core_web_sm")
    STOPWORDS = nlp.Defaults.stop_words
    SPACY_AVAILABLE = True
except:
    print("Warning: spaCy model not found. Please install: python -m spacy download en_core_web_sm")
    SPACY_AVAILABLE = False
    STOPWORDS = set()

@dataclass
class Term:
    term: str
    translation: str
    source: str  # 'builtin' or 'user'

class TerminologyManager:
    def __init__(self, target_lang: str, user_csv_path: str = None, use_builtin: bool = True):
        """
        Initialize terminology manager.
        
        Args:
            target_lang: Target language code (ak, ee, gaa)
            user_csv_path: Path to user's CSV file (optional)
            use_builtin: Whether to use built-in dictionary (default: True)
        """
        self.target_lang = target_lang
        self.terms = {}  # Dictionary: english_term -> translation
        self.sources = {}  # Dictionary: english_term -> source
        
        if use_builtin:
            self._load_builtin_terms()
        
        if user_csv_path:
            self._load_user_terms(user_csv_path)
    
    def _load_builtin_terms(self):
        """Load built-in terms from pickle file."""
        try:
            # Determine which built-in file to load
            if self.target_lang == 'ak':
                pkl_name = 'nouns_ak.pkl'
            elif self.target_lang == 'ee':
                pkl_name = 'nouns_ee.pkl'
            elif self.target_lang == 'gaa':
                pkl_name = 'nouns_gaa.pkl'
            else:
                print(f"Warning: No built-in dictionary for language '{self.target_lang}'")
                return
            
            # Load from package data
            pkl_path = pkg_resources.resource_filename('nkrane_gt', f'data/{pkl_name}')
            
            if os.path.exists(pkl_path):
                with open(pkl_path, 'rb') as f:
                    builtin_dict = pickle.load(f)
                
                # Add built-in terms
                for english_term, translation in builtin_dict.items():
                    english_term_lower = english_term.lower()
                    self.terms[english_term_lower] = translation
                    self.sources[english_term_lower] = 'builtin'
                
                print(f"Loaded {len(builtin_dict)} built-in terms for {self.target_lang}")
            else:
                print(f"Warning: Built-in dictionary not found: {pkl_path}")
                
        except Exception as e:
            print(f"Error loading built-in dictionary: {e}")
    
    def _load_user_terms(self, csv_path: str):
        """Load user terms from CSV file."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Try to detect the delimiter
                sample = f.read(1024)
                f.seek(0)
                
                # Check for common delimiters
                if ',' in sample:
                    delimiter = ','
                elif ';' in sample:
                    delimiter = ';'
                elif '\t' in sample:
                    delimiter = '\t'
                else:
                    delimiter = ','  # default
                
                reader = csv.DictReader(f, delimiter=delimiter)
                fieldnames = [f.lower() for f in reader.fieldnames] if reader.fieldnames else []
                
                # Determine which columns to use
                text_col = None
                trans_col = None
                
                # Look for text column
                for col in ['text', 'english', 'source', 'term', 'word']:
                    if col in fieldnames:
                        text_col = col
                        break
                
                # Look for translation column
                for col in ['text_translated', 'translation', 'target', 'translated']:
                    if col in fieldnames:
                        trans_col = col
                        break
                
                # If not found, use first two columns
                if not text_col or not trans_col:
                    if len(fieldnames) >= 2:
                        text_col = reader.fieldnames[0]
                        trans_col = reader.fieldnames[1]
                    else:
                        print(f"Error: CSV needs at least 2 columns")
                        return
                
                # Read terms
                user_terms_count = 0
                for row in reader:
                    english_term = row.get(text_col, '').strip().lower()
                    translation = row.get(trans_col, '').strip()
                    
                    if english_term and translation:
                        self.terms[english_term] = translation
                        self.sources[english_term] = 'user'
                        user_terms_count += 1
                
                print(f"Loaded {user_terms_count} user terms from {csv_path}")
                
        except Exception as e:
            print(f"Error loading user CSV: {e}")
    
    def _remove_stopwords(self, phrase: str) -> str:
        """Remove stopwords from a phrase."""
        if not SPACY_AVAILABLE:
            # Simple fallback
            words = phrase.lower().split()
            filtered_words = [w for w in words if w not in STOPWORDS]
            return ' '.join(filtered_words)
        
        doc = nlp(phrase.lower())
        cleaned_tokens = [token.text for token in doc if token.text not in STOPWORDS]
        return ' '.join(cleaned_tokens).strip()
    
    def _extract_noun_phrases(self, text: str) -> List[Dict]:
        """Extract noun phrases from text using spaCy."""
        if not SPACY_AVAILABLE:
            # Fallback: extract words that are in our dictionary
            words = re.findall(r'\b\w+\b', text.lower())
            result = []
            for word in words:
                if word in self.terms:
                    # Find position in original text
                    start = text.lower().find(word)
                    if start != -1:
                        result.append({
                            'text': word,
                            'start': start,
                            'end': start + len(word)
                        })
            return result
        
        doc = nlp(text)
        noun_phrases = []
        
        # Extract noun chunks
        for chunk in doc.noun_chunks:
            noun_phrases.append({
                'text': chunk.text,
                'start': chunk.start_char,
                'end': chunk.end_char,
                'root': chunk.root.text
            })
        
        # Also extract standalone proper nouns
        covered_spans = set()
        for np in noun_phrases:
            for i in range(np['start'], np['end']):
                covered_spans.add(i)
        
        for token in doc:
            if token.pos_ in ["PROPN", "NOUN"] and token.idx not in covered_spans:
                noun_phrases.append({
                    'text': token.text,
                    'start': token.idx,
                    'end': token.idx + len(token.text),
                    'root': token.text
                })
        
        return noun_phrases
    
    def preprocess_text(self, text: str) -> Tuple[str, Dict[str, str], Dict[str, str]]:
        """
        Replace noun phrases in text with placeholders.
        Only replaces phrases that are found in terminology.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (preprocessed_text, placeholder_to_translation, original_cases)
        """
        if not self.terms:
            return text, {}, {}
        
        # Split text into sentences
        if SPACY_AVAILABLE:
            doc = nlp(text)
            sentences = [sent.text for sent in doc.sents]
        else:
            # Simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
        
        all_replacements = {}
        all_original_cases = {}
        processed_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                processed_sentences.append(sentence)
                continue
            
            # Extract noun phrases from this sentence
            noun_phrases = self._extract_noun_phrases(sentence)
            
            # Filter to only phrases found in our dictionary
            matching_phrases = []
            for phrase in noun_phrases:
                phrase_lower = phrase['text'].lower()
                # Try exact match first
                if phrase_lower in self.terms:
                    matching_phrases.append(phrase)
                else:
                    # Try without stopwords
                    cleaned = self._remove_stopwords(phrase_lower)
                    if cleaned and cleaned in self.terms:
                        matching_phrases.append({
                            'text': cleaned,
                            'start': phrase['start'],
                            'end': phrase['end']
                        })
            
            # Sort by position (end to start) to avoid replacement issues
            matching_phrases.sort(key=lambda x: x['start'], reverse=True)
            
            preprocessed_sentence = sentence
            sentence_replacements = {}
            sentence_original_cases = {}
            
            for idx, phrase in enumerate(matching_phrases, 1):
                phrase_lower = phrase['text'].lower()
                translation = self.terms.get(phrase_lower)
                
                if translation:
                    placeholder = f"<{idx}>"
                    
                    # Replace in sentence
                    preprocessed_sentence = (
                        preprocessed_sentence[:phrase['start']] + 
                        placeholder + 
                        preprocessed_sentence[phrase['end']:]
                    )
                    
                    sentence_replacements[placeholder] = translation
                    sentence_original_cases[placeholder] = phrase['text']
            
            processed_sentences.append(preprocessed_sentence)
            all_replacements.update(sentence_replacements)
            all_original_cases.update(sentence_original_cases)
        
        # Reconstruct text with processed sentences
        if SPACY_AVAILABLE:
            # Join with original punctuation
            preprocessed_text = ' '.join(processed_sentences)
        else:
            # Simple join
            preprocessed_text = '. '.join(processed_sentences) + '.'
        
        return preprocessed_text, all_replacements, all_original_cases
    
    def postprocess_text(self, text: str, replacements: Dict[str, str], 
                        original_cases: Dict[str, str]) -> str:
        """
        Replace placeholders with translations, preserving case.
        
        Args:
            text: Translated text with placeholders
            replacements: Mapping from placeholders to translations
            original_cases: Mapping from placeholders to original text for case matching
            
        Returns:
            Postprocessed text with actual translations
        """
        result = text
        
        for placeholder, translation in replacements.items():
            original_text = original_cases.get(placeholder, '')
            
            # Preserve original case pattern
            if original_text:
                if original_text.isupper():
                    translation = translation.upper()
                elif original_text.istitle():
                    translation = translation.title()
                elif original_text[0].isupper():
                    translation = translation[0].upper() + translation[1:]
            
            result = result.replace(placeholder, translation)
        
        return result
    
    def get_terms_count(self) -> Dict[str, int]:
        """Get count of terms by source."""
        counts = {'total': len(self.terms), 'builtin': 0, 'user': 0}
        for source in self.sources.values():
            counts[source] += 1
        return counts
