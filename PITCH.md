# Fråga 1177 - Pitch Document

## 1. The Problem

Accessing reliable, personalized healthcare information in Sweden is challenging for both patients and healthcare professionals:

- **Information Overload**: 1177.se contains thousands of medical articles, making it difficult to find relevant, accurate information quickly
- **Lack of Personalization**: General health information doesn't account for individual patient history, lab results, or medical conditions
- **Language Barriers**: Healthcare information needs to be accessible to diverse populations, including non-native Swedish speakers
- **Time Constraints**: Healthcare professionals need quick access to evidence-based information during patient consultations
- **Fragmented Data**: Patient medical history (lab results, imaging, diagnoses) is scattered across different systems and not easily integrated with general health guidance

These challenges lead to delayed care, misunderstandings, and inefficient use of healthcare resources.

---

## 2. The Solution

**Fråga 1177** is an AI-powered healthcare assistant that combines:

### Intelligent Document Search
- **Two-Stage AI Pipeline**: Uses Google Gemini to first identify relevant documents from 1177.se's extensive knowledge base (599+ articles for residents, 120+ for healthcare staff), then generates accurate, contextual answers
- **Parallel Processing**: Efficiently processes hundreds of documents simultaneously to provide fast responses
- **Strict Relevance Filtering**: Ensures only directly relevant medical information is used, preventing misinformation

### Personalized Healthcare Guidance
- **Journal Integration**: Combines general 1177.se information with patient-specific medical history (lab results, imaging, diagnoses, treatment history)
- **Contextual Understanding**: Recognizes patterns in patient data (e.g., "You have a history of fractures, which may be relevant to your current concern")
- **Clarifying Questions**: Asks targeted follow-up questions when queries are ambiguous, ensuring accurate responses

### Accessibility & Trust
- **Source Citations**: Every answer includes direct links to the original 1177.se articles, ensuring transparency and allowing users to verify information
- **Multi-Audience Support**: Tailored responses for both residents (invanare) and healthcare professionals (personal)
- **Multi-Language Ready**: Infrastructure supports Swedish, English, Arabic, and Finnish

### Smart Follow-Up Handling
- **Conversation Context**: Maintains conversation history to provide coherent follow-up responses
- **Cached Document Retrieval**: Optimizes performance by reusing relevant documents for follow-up questions on the same topic

---

## 3. Our Project

**Fråga 1177** is a full-stack AI healthcare assistant built with modern technologies:

### Architecture

**Backend (FastAPI + Python)**
- Context-Augmented Generation (CAG) pipeline using Google Gemini 2.0 Flash
- Parallel batch processing for efficient document analysis
- Two LLM stages: relevance filtering (LLM1) and answer generation (LLM2)
- Journal data processing and formatting
- RESTful API endpoints for chat and journal integration

**Frontend (Next.js + TypeScript)**
- Modern, responsive chat interface
- Real-time conversation with clarifying questions
- Journal data visualization
- Citation preview and source links
- Theme and audience switching (residents/healthcare staff)

**Data Infrastructure**
- 599+ markdown documents from 1177.se for residents
- 120+ documents for healthcare professionals
- Structured patient journal data (labs, imaging, medical history)
- Metadata extraction (URLs, titles) for source citations

### Key Features

1. **Intelligent Question Answering**
   - Natural language queries about health concerns
   - Automatic document retrieval from 1177.se knowledge base
   - Contextual answers with source citations

2. **Personalized Responses**
   - Integration with patient medical journals
   - References to patient history when relevant
   - Combines general knowledge with personal context

3. **Clarifying Questions**
   - Up to 2 rounds of clarifying questions for ambiguous queries
   - Multiple-choice options for better user experience
   - Ensures accurate, relevant responses

4. **Performance Optimizations**
   - Parallel document processing (up to 20 concurrent workers)
   - Cached document retrieval for follow-up questions
   - Efficient batch processing of large document sets

5. **Developer-Friendly**
   - Comprehensive logging and debugging
   - Modular, maintainable codebase
   - Easy configuration and deployment

### Technology Stack

- **AI/ML**: Google Gemini 2.0 Flash
- **Backend**: FastAPI, Python 3.8+
- **Frontend**: Next.js, React, TypeScript
- **Styling**: Tailwind CSS
- **Text-to-Speech**: ElevenLabs (optional)
- **Data Format**: JSON, Markdown

### Impact

**For Patients/Residents:**
- Quick access to reliable health information
- Personalized guidance based on medical history
- Clear source citations for verification
- Reduced anxiety through better understanding

**For Healthcare Professionals:**
- Rapid access to evidence-based information
- Integration with patient data for informed decisions
- Time-saving during consultations
- Consistent, accurate information delivery

**For the Healthcare System:**
- Reduced unnecessary visits through better self-care guidance
- Improved patient education and engagement
- More efficient use of healthcare resources
- Better health outcomes through informed decision-making

---

## Vision

**Fråga 1177** aims to democratize access to reliable healthcare information by combining the comprehensive knowledge base of 1177.se with the power of AI and personalization. We envision a future where every Swede has instant, personalized access to trustworthy health guidance, and healthcare professionals have an intelligent assistant to support their clinical decision-making.
