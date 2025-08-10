"""
Performance optimization service for database and file operations
"""
import time
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, scoped_session
from app import db

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_timing(self, operation: str, duration: float):
        """Record timing for an operation"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'avg_time': 0
            }
        
        metric = self.metrics[operation]
        metric['count'] += 1
        metric['total_time'] += duration
        metric['min_time'] = min(metric['min_time'], duration)
        metric['max_time'] = max(metric['max_time'], duration)
        metric['avg_time'] = metric['total_time'] / metric['count']
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()

# Global performance monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                performance_monitor.record_timing(op_name, duration)
                
                if duration > 1.0:  # Log slow operations
                    logger.warning(f"Slow operation {op_name}: {duration:.2f}s")
                elif duration > 0.1:
                    logger.info(f"Operation {op_name}: {duration:.2f}s")
        
        return wrapper
    return decorator

class DatabaseOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def get_connection_pool_status():
        """Get database connection pool status"""
        engine = db.engine
        pool = engine.pool
        
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }
    
    @staticmethod
    def optimize_query_plan(query_sql: str) -> Dict[str, Any]:
        """Analyze query execution plan"""
        try:
            explain_query = f"EXPLAIN QUERY PLAN {query_sql}"
            result = db.session.execute(text(explain_query))
            
            plan_rows = []
            for row in result:
                plan_rows.append({
                    'id': row[0],
                    'parent': row[1],
                    'notused': row[2],
                    'detail': row[3]
                })
            
            return {
                'query': query_sql,
                'plan': plan_rows,
                'analysis': DatabaseOptimizer._analyze_plan(plan_rows)
            }
        except Exception as e:
            logger.error(f"Error analyzing query plan: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_plan(plan_rows: List[Dict]) -> Dict[str, Any]:
        """Analyze query plan for optimization opportunities"""
        analysis = {
            'has_index_scan': False,
            'has_table_scan': False,
            'join_count': 0,
            'recommendations': []
        }
        
        for row in plan_rows:
            detail = row['detail'].lower()
            
            if 'using index' in detail:
                analysis['has_index_scan'] = True
            elif 'scan table' in detail:
                analysis['has_table_scan'] = True
                analysis['recommendations'].append(
                    f"Consider adding index for table scan: {detail}"
                )
            
            if 'join' in detail:
                analysis['join_count'] += 1
        
        if analysis['join_count'] > 3:
            analysis['recommendations'].append(
                "High number of joins detected, consider query optimization"
            )
        
        return analysis
    
    @staticmethod
    def get_table_stats() -> Dict[str, Any]:
        """Get database table statistics"""
        try:
            # Get table sizes and row counts
            stats_query = """
            SELECT 
                name as table_name,
                (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=m.name) as index_count
            FROM sqlite_master m 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            
            result = db.session.execute(text(stats_query))
            tables = []
            
            for row in result:
                table_name = row[0]
                index_count = row[1]
                
                # Get row count
                count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar()
                
                tables.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'index_count': index_count
                })
            
            return {'tables': tables}
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {'error': str(e)}

class FileSystemOptimizer:
    """File system operation optimization utilities"""
    
    @staticmethod
    @monitor_performance("file_batch_read")
    def batch_read_files(file_paths: List[str]) -> Dict[str, Optional[str]]:
        """Read multiple files in batch for better performance"""
        results = {}
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    results[file_path] = f.read()
            except (IOError, OSError) as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                results[file_path] = None
        
        return results
    
    @staticmethod
    @monitor_performance("file_batch_write")
    def batch_write_files(file_data: Dict[str, str]) -> Dict[str, bool]:
        """Write multiple files in batch for better performance"""
        results = {}
        
        for file_path, content in file_data.items():
            try:
                # Ensure directory exists
                import os
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                results[file_path] = True
            except (IOError, OSError) as e:
                logger.error(f"Failed to write file {file_path}: {e}")
                results[file_path] = False
        
        return results
    
    @staticmethod
    def get_directory_stats(directory_path: str) -> Dict[str, Any]:
        """Get directory statistics for optimization"""
        import os
        
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'file_types': {},
                'large_files': [],
                'empty_files': []
            }
            
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        stats['total_files'] += 1
                        stats['total_size'] += file_size
                        
                        # Track file types
                        if file_ext not in stats['file_types']:
                            stats['file_types'][file_ext] = {'count': 0, 'size': 0}
                        stats['file_types'][file_ext]['count'] += 1
                        stats['file_types'][file_ext]['size'] += file_size
                        
                        # Track large files (>1MB)
                        if file_size > 1024 * 1024:
                            stats['large_files'].append({
                                'path': file_path,
                                'size': file_size
                            })
                        
                        # Track empty files
                        if file_size == 0:
                            stats['empty_files'].append(file_path)
                    
                    except OSError:
                        continue
            
            return stats
        except Exception as e:
            logger.error(f"Error getting directory stats: {e}")
            return {'error': str(e)}

# Optimized database session management
class OptimizedSession:
    """Context manager for optimized database sessions"""
    
    def __init__(self, autocommit=False):
        self.autocommit = autocommit
        self.session = None
    
    def __enter__(self):
        self.session = db.session
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None and self.autocommit:
                self.session.commit()
            elif exc_type is not None:
                self.session.rollback()
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
            self.session.rollback()

def bulk_insert_optimized(model_class, data_list: List[Dict], batch_size: int = 100):
    """Optimized bulk insert for large datasets"""
    if not data_list:
        return
    
    with OptimizedSession(autocommit=True) as session:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            session.bulk_insert_mappings(model_class, batch)
            
            # Commit each batch to avoid memory issues
            if i + batch_size < len(data_list):
                session.commit()

def bulk_update_optimized(model_class, data_list: List[Dict], batch_size: int = 100):
    """Optimized bulk update for large datasets"""
    if not data_list:
        return
    
    with OptimizedSession(autocommit=True) as session:
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            session.bulk_update_mappings(model_class, batch)
            
            # Commit each batch to avoid memory issues
            if i + batch_size < len(data_list):
                session.commit()