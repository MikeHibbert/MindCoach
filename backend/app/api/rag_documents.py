"""
API endpoints for RAG document management
"""
import logging
from flask import Blueprint, jsonify, request
from app.services.rag_document_service import rag_service

logger = logging.getLogger(__name__)

rag_docs_bp = Blueprint('rag_docs', __name__)

@rag_docs_bp.route('/rag-docs', methods=['GET'])
def list_available_documents():
    """List all available RAG documents"""
    try:
        available_docs = rag_service.get_available_documents()
        stats = rag_service.get_document_stats()
        
        return jsonify({
            'status': 'success',
            'available_documents': available_docs,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list RAG documents: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rag_docs_bp.route('/rag-docs/<doc_type>', methods=['GET'])
def get_document(doc_type):
    """Get a specific RAG document"""
    try:
        subject = request.args.get('subject')
        
        content = rag_service.load_document(doc_type, subject)
        
        if not content:
            return jsonify({
                'status': 'error',
                'message': f'Document not found: {doc_type}' + (f' for subject {subject}' if subject else '')
            }), 404
        
        return jsonify({
            'status': 'success',
            'document_type': doc_type,
            'subject': subject,
            'content': content,
            'content_length': len(content)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get RAG document {doc_type}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rag_docs_bp.route('/rag-docs/<doc_type>/validate', methods=['POST'])
def validate_document(doc_type):
    """Validate a RAG document structure"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if not content:
            # Load existing document if no content provided
            subject = data.get('subject')
            content = rag_service.load_document(doc_type, subject)
            
            if not content:
                return jsonify({
                    'status': 'error',
                    'message': f'No content provided and document not found: {doc_type}'
                }), 400
        
        validation_results = rag_service.validate_document_structure(doc_type, content)
        
        return jsonify({
            'status': 'success',
            'document_type': doc_type,
            'validation_results': validation_results,
            'is_valid': validation_results.get('is_valid', False)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to validate RAG document {doc_type}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rag_docs_bp.route('/rag-docs/stage/<stage>', methods=['GET'])
def get_documents_for_stage(stage):
    """Get all RAG documents for a specific pipeline stage"""
    try:
        subject = request.args.get('subject')
        
        documents = rag_service.load_documents_for_stage(stage, subject)
        
        return jsonify({
            'status': 'success',
            'stage': stage,
            'subject': subject,
            'document_count': len(documents),
            'documents': documents
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get RAG documents for stage {stage}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rag_docs_bp.route('/rag-docs/cache/clear', methods=['POST'])
def clear_document_cache():
    """Clear the RAG document cache"""
    try:
        rag_service.clear_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Document cache cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to clear RAG document cache: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rag_docs_bp.route('/rag-docs/<doc_type>/reload', methods=['POST'])
def reload_document(doc_type):
    """Reload a specific RAG document from disk"""
    try:
        data = request.get_json() or {}
        subject = data.get('subject')
        
        content = rag_service.reload_document(doc_type, subject)
        
        if not content:
            return jsonify({
                'status': 'error',
                'message': f'Document not found: {doc_type}' + (f' for subject {subject}' if subject else '')
            }), 404
        
        return jsonify({
            'status': 'success',
            'message': f'Document reloaded successfully: {doc_type}' + (f' for subject {subject}' if subject else ''),
            'content_length': len(content)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to reload RAG document {doc_type}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@rag_docs_bp.route('/rag-docs/stats', methods=['GET'])
def get_document_statistics():
    """Get detailed statistics about RAG documents"""
    try:
        stats = rag_service.get_document_stats()
        available_docs = rag_service.get_available_documents()
        
        # Add validation stats for all documents
        validation_summary = {}
        for doc_type in available_docs['general']:
            try:
                content = rag_service.load_document(doc_type)
                if content:
                    validation = rag_service.validate_document_structure(doc_type, content)
                    validation_summary[doc_type] = validation.get('is_valid', False)
            except Exception as e:
                logger.warning(f"Could not validate document {doc_type}: {e}")
                validation_summary[doc_type] = False
        
        return jsonify({
            'status': 'success',
            'statistics': stats,
            'validation_summary': validation_summary,
            'total_valid_documents': sum(validation_summary.values()),
            'total_invalid_documents': len(validation_summary) - sum(validation_summary.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get RAG document statistics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500