"""
Semantic Chunker - Intelligent text segmentation for RAG system
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a semantically coherent chunk of text"""
    text: str
    chunk_type: str  # paragraph, section, list_item, table, etc.
    start_position: int
    end_position: int
    metadata: Dict[str, Any]
    confidence: float = 1.0

class SemanticChunker:
    """
    Semantic chunker that intelligently segments text for better RAG retrieval
    """
    
    def __init__(self, max_chunk_size: int = 1000, overlap_size: int = 200):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self._setup_nltk()
        
    def _setup_nltk(self):
        """Setup NLTK components"""
        try:
            # Download required NLTK data
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            logger.warning(f"NLTK setup failed: {e}. Using basic chunking.")
            self.stop_words = set()
    
    async def chunk_document(self, text: str, document_type: str = "general") -> List[TextChunk]:
        """
        Chunk a document into semantically coherent pieces
        
        Args:
            text: Input text to chunk
            document_type: Type of document (article, manual, faq, etc.)
            
        Returns:
            List of text chunks
        """
        try:
            # Pre-process text
            cleaned_text = self._preprocess_text(text)
            
            # Choose chunking strategy based on document type
            if document_type == "manual":
                chunks = await self._chunk_manual(cleaned_text)
            elif document_type == "faq":
                chunks = await self._chunk_faq(cleaned_text)
            elif document_type == "article":
                chunks = await self._chunk_article(cleaned_text)
            else:
                chunks = await self._chunk_general(cleaned_text)
            
            # Post-process chunks
            processed_chunks = self._post_process_chunks(chunks)
            
            logger.info(f"Created {len(processed_chunks)} chunks from {len(text)} characters")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"Document chunking failed: {e}")
            # Fallback to simple chunking
            return await self._simple_chunk(text)
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        # Fix common encoding issues
        text = text.replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
        
        return text.strip()
    
    async def _chunk_manual(self, text: str) -> List[TextChunk]:
        """Chunk technical manual content"""
        chunks = []
        
        # Split by sections (headers)
        sections = re.split(r'\n(?=#+\s)', text)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Extract header if present
            header_match = re.match(r'^(#+\s*)(.+?)(?:\n|$)', section)
            if header_match:
                header = header_match.group(2).strip()
                content = section[header_match.end():].strip()
                chunk_type = f"section_level_{len(header_match.group(1).strip())}"
            else:
                header = f"Section {i+1}"
                content = section
                chunk_type = "section"
            
            # Further split large sections
            if len(content) > self.max_chunk_size:
                sub_chunks = await self._split_large_content(content, chunk_type)
                chunks.extend(sub_chunks)
            else:
                chunk = TextChunk(
                    text=content,
                    chunk_type=chunk_type,
                    start_position=0,
                    end_position=len(content),
                    metadata={"header": header, "section_number": i+1}
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _chunk_faq(self, text: str) -> List[TextChunk]:
        """Chunk FAQ content"""
        chunks = []
        
        # Split by Q&A pairs
        qa_pattern = r'(?:^|\n)(?:Q(?:uestion)?[:\.]?\s*)(.*?)(?=\n(?:A(?:nswer)?[:\.]?\s*))(.*?)(?=\n(?:Q(?:uestion)?[:\.]?)|$)'
        qa_matches = re.finditer(qa_pattern, text, re.MULTILINE | re.DOTALL)
        
        for i, match in enumerate(qa_matches):
            question = match.group(1).strip()
            answer = match.group(2).strip()
            
            full_text = f"Q: {question}\nA: {answer}"
            
            chunk = TextChunk(
                text=full_text,
                chunk_type="qa_pair",
                start_position=match.start(),
                end_position=match.end(),
                metadata={"question": question, "answer": answer, "qa_number": i+1}
            )
            chunks.append(chunk)
        
        # If no Q&A pattern found, fall back to paragraph chunking
        if not chunks:
            return await self._chunk_general(text)
        
        return chunks
    
    async def _chunk_article(self, text: str) -> List[TextChunk]:
        """Chunk article content by paragraphs and sections"""
        chunks = []
        
        # Split by paragraphs
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        chunk_start = 0
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph exceeds max size
            potential_chunk = current_chunk + ("\n\n" if current_chunk else "") + paragraph
            
            if len(potential_chunk) > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    chunk_type="paragraph_group",
                    start_position=chunk_start,
                    end_position=chunk_start + len(current_chunk),
                    metadata={"paragraph_count": current_chunk.count('\n\n') + 1}
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                current_chunk = paragraph
                chunk_start += len(current_chunk) - self.overlap_size
            else:
                current_chunk = potential_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunk = TextChunk(
                text=current_chunk.strip(),
                chunk_type="paragraph_group",
                start_position=chunk_start,
                end_position=chunk_start + len(current_chunk),
                metadata={"paragraph_count": current_chunk.count('\n\n') + 1}
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _chunk_general(self, text: str) -> List[TextChunk]:
        """General purpose chunking strategy"""
        chunks = []
        
        # Try to split by sentences first
        try:
            sentences = sent_tokenize(text)
        except:
            # Fallback if NLTK not available
            sentences = re.split(r'[.!?]+\s+', text)
        
        current_chunk = ""
        chunk_start = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
            
            if len(potential_chunk) > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk = TextChunk(
                    text=current_chunk.strip(),
                    chunk_type="sentence_group",
                    start_position=chunk_start,
                    end_position=chunk_start + len(current_chunk),
                    metadata={"sentence_count": len(sent_tokenize(current_chunk)) if current_chunk else 0}
                )
                chunks.append(chunk)
                
                # Start new chunk with current sentence
                current_chunk = sentence
                chunk_start += len(current_chunk)
            else:
                current_chunk = potential_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunk = TextChunk(
                text=current_chunk.strip(),
                chunk_type="sentence_group", 
                start_position=chunk_start,
                end_position=chunk_start + len(current_chunk),
                metadata={"sentence_count": len(sent_tokenize(current_chunk)) if current_chunk else 0}
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _split_large_content(self, content: str, chunk_type: str) -> List[TextChunk]:
        """Split large content into smaller chunks"""
        chunks = []
        
        # Try sentence-level splitting first
        try:
            sentences = sent_tokenize(content)
        except:
            sentences = re.split(r'[.!?]+\s+', content)
        
        current_text = ""
        start_pos = 0
        
        for sentence in sentences:
            potential_text = current_text + (" " if current_text else "") + sentence
            
            if len(potential_text) > self.max_chunk_size and current_text:
                chunk = TextChunk(
                    text=current_text.strip(),
                    chunk_type=f"{chunk_type}_split",
                    start_position=start_pos,
                    end_position=start_pos + len(current_text),
                    metadata={"split_chunk": True}
                )
                chunks.append(chunk)
                
                current_text = sentence
                start_pos += len(current_text)
            else:
                current_text = potential_text
        
        if current_text.strip():
            chunk = TextChunk(
                text=current_text.strip(),
                chunk_type=f"{chunk_type}_split",
                start_position=start_pos,
                end_position=start_pos + len(current_text),
                metadata={"split_chunk": True}
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _simple_chunk(self, text: str) -> List[TextChunk]:
        """Simple fallback chunking"""
        chunks = []
        
        for i in range(0, len(text), self.max_chunk_size - self.overlap_size):
            chunk_text = text[i:i + self.max_chunk_size]
            
            chunk = TextChunk(
                text=chunk_text,
                chunk_type="simple_chunk",
                start_position=i,
                end_position=i + len(chunk_text),
                metadata={"chunk_index": len(chunks)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _post_process_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """Post-process chunks for quality"""
        processed = []
        
        for chunk in chunks:
            # Skip very short chunks
            if len(chunk.text.strip()) < 50:
                continue
            
            # Calculate confidence score
            confidence = self._calculate_chunk_confidence(chunk)
            chunk.confidence = confidence
            
            processed.append(chunk)
        
        return processed
    
    def _calculate_chunk_confidence(self, chunk: TextChunk) -> float:
        """Calculate confidence score for chunk quality"""
        text = chunk.text
        
        # Base confidence
        confidence = 1.0
        
        # Penalize very short chunks
        if len(text) < 100:
            confidence *= 0.7
        
        # Reward complete sentences
        sentence_endings = len(re.findall(r'[.!?]\s', text))
        if sentence_endings > 0:
            confidence *= 1.1
        
        # Penalize incomplete sentences at boundaries
        if not text.strip().endswith(('.', '!', '?', ':')):
            confidence *= 0.9
        
        # Reward chunks with structured content
        if chunk.chunk_type in ['section', 'qa_pair']:
            confidence *= 1.2
        
        return min(1.0, confidence)