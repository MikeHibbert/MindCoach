"""
Pipeline orchestration service for managing three-stage LangChain workflow
with progress tracking, error handling, and background task processing
"""
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from .langchain_pipeline import LangChainPipelineService
from .user_data_service import UserDataService
from .file_service import FileService

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """Pipeline stage enumeration"""
    SURVEY_GENERATION = "survey_generation"
    CURRICULUM_GENERATION = "curriculum_generation"
    LESSON_PLANNING = "lesson_planning"
    CONTENT_GENERATION = "content_generation"

class PipelineStatus(Enum):
    """Pipeline status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PipelineProgress:
    """Data class for tracking pipeline progress"""
    user_id: str
    subject: str
    current_stage: PipelineStage
    status: PipelineStatus
    progress_percentage: float
    stages_completed: int
    total_stages: int
    current_step: str
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to strings
        result['current_stage'] = self.current_stage.value
        result['status'] = self.status.value
        return result

class PipelineOrchestrator:
    """
    Orchestrates the three-stage LangChain content generation pipeline
    with progress tracking, error handling, and recovery mechanisms
    """
    
    def __init__(self):
        """Initialize the pipeline orchestrator"""
        self.pipeline_service = LangChainPipelineService()
        self.active_pipelines: Dict[str, PipelineProgress] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        logger.info("Pipeline orchestrator initialized")
    
    def start_full_pipeline(
        self, 
        user_id: str, 
        subject: str, 
        survey_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        Start the complete three-stage pipeline for a user and subject
        
        Args:
            user_id: User identifier
            subject: Subject for content generation
            survey_data: Survey results to base curriculum on
            progress_callback: Optional callback for progress updates
            
        Returns:
            Pipeline ID for tracking progress
        """
        pipeline_id = f"{user_id}_{subject}_{int(time.time())}"
        
        # Initialize progress tracking
        progress = PipelineProgress(
            user_id=user_id,
            subject=subject,
            current_stage=PipelineStage.CURRICULUM_GENERATION,
            status=PipelineStatus.IN_PROGRESS,
            progress_percentage=0.0,
            stages_completed=0,
            total_stages=3,
            current_step="Initializing pipeline",
            started_at=datetime.utcnow().isoformat() + 'Z'
        )
        
        self.active_pipelines[pipeline_id] = progress
        
        if progress_callback:
            if pipeline_id not in self.progress_callbacks:
                self.progress_callbacks[pipeline_id] = []
            self.progress_callbacks[pipeline_id].append(progress_callback)
        
        logger.info(f"Starting full pipeline {pipeline_id} for user {user_id}, subject {subject}")
        
        try:
            # Execute pipeline stages in background (for now, we'll run synchronously but add better error handling)
            import threading
            
            def run_pipeline():
                try:
                    self._execute_pipeline_stages(pipeline_id, survey_data)
                except Exception as e:
                    logger.error(f"Pipeline {pipeline_id} failed: {e}")
                    progress.status = PipelineStatus.FAILED
                    progress.error_message = str(e)
                    self._notify_progress_update(pipeline_id)
            
            # Start pipeline in background thread
            pipeline_thread = threading.Thread(target=run_pipeline, daemon=True)
            pipeline_thread.start()
            
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} startup failed: {e}")
            progress.status = PipelineStatus.FAILED
            progress.error_message = str(e)
            self._notify_progress_update(pipeline_id)
            raise
        
        return pipeline_id
    
    def _execute_pipeline_stages(self, pipeline_id: str, survey_data: Dict[str, Any]):
        """Execute all pipeline stages with progress tracking"""
        progress = self.active_pipelines[pipeline_id]
        user_id = progress.user_id
        subject = progress.subject
        
        logger.info(f"Starting pipeline execution for {pipeline_id}: user={user_id}, subject={subject}")
        
        try:
            # Load RAG documents for all stages
            logger.info(f"Loading RAG documents for {subject}")
            rag_docs = self._load_all_rag_documents(subject)
            logger.info(f"RAG documents loaded: {len(rag_docs.get('curriculum', []))} curriculum, {len(rag_docs.get('lesson_plans', []))} lesson_plans, {len(rag_docs.get('content', []))} content")
            
            # Stage 1: Curriculum Generation
            logger.info(f"Starting Stage 1: Curriculum Generation for {pipeline_id}")
            self._update_progress(
                pipeline_id, 
                PipelineStage.CURRICULUM_GENERATION,
                "Generating curriculum scheme",
                0.0
            )
            
            logger.info(f"Calling curriculum generation with survey data keys: {list(survey_data.keys())}")
            curriculum_data = self.pipeline_service.generate_curriculum(
                survey_data, subject, rag_docs.get('curriculum', [])
            )
            logger.info(f"Curriculum generation completed for {pipeline_id}")
            
            # Save curriculum data
            UserDataService.save_curriculum_scheme(user_id, subject, curriculum_data)
            
            self._update_progress(
                pipeline_id,
                PipelineStage.CURRICULUM_GENERATION,
                "Curriculum generation completed",
                33.3,
                stages_completed=1
            )
            
            # Stage 2: Lesson Planning
            self._update_progress(
                pipeline_id,
                PipelineStage.LESSON_PLANNING,
                "Creating detailed lesson plans",
                33.3
            )
            
            lesson_plans_data = self.pipeline_service.generate_lesson_plans(
                curriculum_data, subject, rag_docs.get('lesson_plans', [])
            )
            
            # Save lesson plans data
            UserDataService.save_lesson_plans(user_id, subject, lesson_plans_data)
            
            self._update_progress(
                pipeline_id,
                PipelineStage.LESSON_PLANNING,
                "Lesson planning completed",
                66.6,
                stages_completed=2
            )
            
            # Stage 3: Content Generation
            self._update_progress(
                pipeline_id,
                PipelineStage.CONTENT_GENERATION,
                "Generating lesson content",
                66.6
            )
            
            lesson_plans = lesson_plans_data.get('lesson_plans', [])
            total_lessons = len(lesson_plans)
            
            for i, lesson_plan in enumerate(lesson_plans):
                lesson_id = lesson_plan.get('lesson_id', i + 1)
                
                # Update progress for current lesson
                lesson_progress = 66.6 + (33.3 * (i / total_lessons))
                self._update_progress(
                    pipeline_id,
                    PipelineStage.CONTENT_GENERATION,
                    f"Generating lesson {lesson_id} content ({i + 1}/{total_lessons})",
                    lesson_progress
                )
                
                # Generate lesson content
                lesson_content = self.pipeline_service.generate_lesson_content(
                    lesson_plan, subject, rag_docs.get('content', [])
                )
                
                # Save lesson content
                UserDataService.save_lesson_content(user_id, subject, lesson_id, lesson_content)
            
            # Pipeline completed successfully
            self._update_progress(
                pipeline_id,
                PipelineStage.CONTENT_GENERATION,
                "All content generation completed",
                100.0,
                stages_completed=3,
                status=PipelineStatus.COMPLETED
            )
            
            progress.completed_at = datetime.utcnow().isoformat() + 'Z'
            
            logger.info(f"Pipeline {pipeline_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} execution failed: {e}")
            progress.status = PipelineStatus.FAILED
            progress.error_message = str(e)
            self._notify_progress_update(pipeline_id)
            raise
    
    def _load_all_rag_documents(self, subject: str) -> Dict[str, List[str]]:
        """Load RAG documents for all pipeline stages"""
        from .rag_document_service import rag_service
        
        return {
            'curriculum': rag_service.load_documents_for_stage('curriculum', subject),
            'lesson_plans': rag_service.load_documents_for_stage('lesson_plans', subject),
            'content': rag_service.load_documents_for_stage('content', subject)
        }
    
    def _update_progress(
        self, 
        pipeline_id: str, 
        stage: PipelineStage, 
        step: str, 
        percentage: float,
        stages_completed: Optional[int] = None,
        status: Optional[PipelineStatus] = None
    ):
        """Update pipeline progress and notify callbacks"""
        if pipeline_id not in self.active_pipelines:
            return
        
        progress = self.active_pipelines[pipeline_id]
        progress.current_stage = stage
        progress.current_step = step
        progress.progress_percentage = percentage
        
        if stages_completed is not None:
            progress.stages_completed = stages_completed
        
        if status is not None:
            progress.status = status
        
        # Calculate estimated completion time
        if percentage > 0 and progress.started_at:
            elapsed_time = time.time() - datetime.fromisoformat(progress.started_at.replace('Z', '')).timestamp()
            estimated_total_time = elapsed_time * (100 / percentage)
            estimated_remaining = estimated_total_time - elapsed_time
            
            if estimated_remaining > 0:
                estimated_completion = datetime.fromtimestamp(
                    time.time() + estimated_remaining
                ).isoformat() + 'Z'
                progress.estimated_completion = estimated_completion
        
        self._notify_progress_update(pipeline_id)
        
        logger.debug(f"Pipeline {pipeline_id} progress: {percentage:.1f}% - {step}")
    
    def _notify_progress_update(self, pipeline_id: str):
        """Notify all registered callbacks about progress update"""
        if pipeline_id in self.progress_callbacks:
            progress = self.active_pipelines[pipeline_id]
            for callback in self.progress_callbacks[pipeline_id]:
                try:
                    callback(progress.to_dict())
                except Exception as e:
                    logger.warning(f"Progress callback failed for {pipeline_id}: {e}")
    
    def get_pipeline_progress(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress for a pipeline"""
        if pipeline_id not in self.active_pipelines:
            return None
        
        return self.active_pipelines[pipeline_id].to_dict()
    
    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline"""
        if pipeline_id not in self.active_pipelines:
            return False
        
        progress = self.active_pipelines[pipeline_id]
        if progress.status == PipelineStatus.IN_PROGRESS:
            progress.status = PipelineStatus.CANCELLED
            progress.error_message = "Pipeline cancelled by user"
            self._notify_progress_update(pipeline_id)
            
            logger.info(f"Pipeline {pipeline_id} cancelled")
            return True
        
        return False
    
    def cleanup_completed_pipelines(self, max_age_hours: int = 24):
        """Clean up completed pipelines older than specified hours"""
        current_time = time.time()
        to_remove = []
        
        for pipeline_id, progress in self.active_pipelines.items():
            if progress.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED, PipelineStatus.CANCELLED]:
                if progress.completed_at:
                    completed_time = datetime.fromisoformat(progress.completed_at.replace('Z', '')).timestamp()
                    if (current_time - completed_time) > (max_age_hours * 3600):
                        to_remove.append(pipeline_id)
        
        for pipeline_id in to_remove:
            del self.active_pipelines[pipeline_id]
            if pipeline_id in self.progress_callbacks:
                del self.progress_callbacks[pipeline_id]
            
            logger.debug(f"Cleaned up old pipeline {pipeline_id}")
    
    def get_active_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """Get all active pipelines"""
        return {
            pipeline_id: progress.to_dict() 
            for pipeline_id, progress in self.active_pipelines.items()
        }
    
    def retry_failed_pipeline(self, pipeline_id: str) -> bool:
        """Retry a failed pipeline from the last successful stage"""
        if pipeline_id not in self.active_pipelines:
            return False
        
        progress = self.active_pipelines[pipeline_id]
        if progress.status != PipelineStatus.FAILED:
            return False
        
        logger.info(f"Retrying failed pipeline {pipeline_id}")
        
        # Reset status and error
        progress.status = PipelineStatus.IN_PROGRESS
        progress.error_message = None
        
        try:
            # Load survey data for retry
            survey_data = UserDataService.load_survey_answers(progress.user_id, progress.subject)
            if not survey_data:
                raise ValueError("Survey data not found for retry")
            
            # Continue from where it failed
            self._execute_pipeline_stages(pipeline_id, survey_data)
            return True
            
        except Exception as e:
            logger.error(f"Pipeline retry {pipeline_id} failed: {e}")
            progress.status = PipelineStatus.FAILED
            progress.error_message = str(e)
            self._notify_progress_update(pipeline_id)
            return False
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get statistics about pipeline usage"""
        total_pipelines = len(self.active_pipelines)
        status_counts = {}
        
        for progress in self.active_pipelines.values():
            status = progress.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_pipelines': total_pipelines,
            'status_distribution': status_counts,
            'active_count': status_counts.get('in_progress', 0),
            'completed_count': status_counts.get('completed', 0),
            'failed_count': status_counts.get('failed', 0)
        }

# Global orchestrator instance (lazy-loaded)
_pipeline_orchestrator = None

def get_pipeline_orchestrator() -> PipelineOrchestrator:
    """Get or create the global pipeline orchestrator instance"""
    global _pipeline_orchestrator
    if _pipeline_orchestrator is None:
        _pipeline_orchestrator = PipelineOrchestrator()
    return _pipeline_orchestrator