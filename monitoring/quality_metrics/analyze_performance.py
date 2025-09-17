#!/usr/bin/env python3
"""
Agentic AI RAG Pipeline - Performance Analysis
Analyzes quality metrics and agent performance from S3 data
"""

import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

class AgentPerformanceAnalyzer:
    def __init__(self, bucket_name='support-agent-search-results'):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name
        
    def load_quality_metrics(self, days_back=7):
        """Load quality metrics from S3 for analysis"""
        metrics = []
        
        # Generate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # List objects in S3 with date partitioning
        for i in range(days_back):
            date = start_date + timedelta(days=i)
            prefix = f"rag-quality-metrics/{date.strftime('%Y/%m/%d')}/"
            
            try:
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                for obj in response.get('Contents', []):
                    # Load metric file
                    metric_data = self.s3.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    
                    metric = json.loads(metric_data['Body'].read())
                    metrics.append(metric)
                    
            except Exception as e:
                print(f"Error loading metrics for {date}: {e}")
                
        return pd.DataFrame(metrics)
    
    def analyze_agent_performance(self, df):
        """Analyze performance of each agent"""
        if df.empty:
            print("No data available for analysis")
            return
            
        print("🤖 Agent Performance Analysis")
        print("=" * 50)
        
        # Overall statistics
        print(f"📊 Total Queries Analyzed: {len(df)}")
        print(f"📅 Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Quality metrics
        if 'quality_metrics' in df.columns:
            quality_df = pd.json_normalize(df['quality_metrics'])
            
            print(f"\n📈 Quality Metrics:")
            print(f"   Average Score: {quality_df['avg_score'].mean():.3f}")
            print(f"   Score Variance: {quality_df['score_variance'].mean():.3f}")
            print(f"   Average Results: {quality_df['result_count'].mean():.1f}")
        
        # Pipeline performance
        if 'pipeline_performance' in df.columns:
            pipeline_data = []
            for _, row in df.iterrows():
                for stage in row['pipeline_performance']:
                    if isinstance(stage, dict):
                        pipeline_data.append(stage)
            
            pipeline_df = pd.DataFrame(pipeline_data)
            
            if not pipeline_df.empty:
                print(f"\n⚡ Pipeline Performance by Stage:")
                stage_performance = pipeline_df.groupby('stage').agg({
                    'processing_time_ms': ['mean', 'std', 'count'],
                    'input_count': 'mean',
                    'output_count': 'mean'
                }).round(2)
                
                print(stage_performance)
        
        # Parameter analysis
        if 'parameters' in df.columns:
            params_df = pd.json_normalize(df['parameters'])
            
            print(f"\n🔧 Parameter Usage:")
            if 'use_reranker' in params_df.columns:
                reranker_usage = params_df['use_reranker'].value_counts()
                print(f"   Reranker Usage: {reranker_usage.to_dict()}")
            
            if 'use_mmr' in params_df.columns:
                mmr_usage = params_df['use_mmr'].value_counts()
                print(f"   MMR Usage: {mmr_usage.to_dict()}")
    
    def generate_performance_plots(self, df):
        """Generate performance visualization plots"""
        if df.empty:
            return
            
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Agentic AI RAG Pipeline - Performance Analysis', fontsize=16)
        
        # Quality scores over time
        if 'quality_metrics' in df.columns:
            quality_df = pd.json_normalize(df['quality_metrics'])
            quality_df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            axes[0, 0].plot(quality_df['timestamp'], quality_df['avg_score'])
            axes[0, 0].set_title('Average Quality Score Over Time')
            axes[0, 0].set_ylabel('Score')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Result count distribution
        if 'quality_metrics' in df.columns:
            axes[0, 1].hist(quality_df['result_count'], bins=20, alpha=0.7)
            axes[0, 1].set_title('Result Count Distribution')
            axes[0, 1].set_xlabel('Number of Results')
            axes[0, 1].set_ylabel('Frequency')
        
        # Pipeline stage performance
        if 'pipeline_performance' in df.columns:
            pipeline_data = []
            for _, row in df.iterrows():
                for stage in row['pipeline_performance']:
                    if isinstance(stage, dict) and 'stage' in stage:
                        pipeline_data.append(stage)
            
            if pipeline_data:
                pipeline_df = pd.DataFrame(pipeline_data)
                stage_times = pipeline_df.groupby('stage')['processing_time_ms'].mean()
                
                axes[1, 0].bar(stage_times.index, stage_times.values)
                axes[1, 0].set_title('Average Processing Time by Stage')
                axes[1, 0].set_ylabel('Time (ms)')
                axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Parameter effectiveness
        if 'parameters' in df.columns and 'quality_metrics' in df.columns:
            params_df = pd.json_normalize(df['parameters'])
            quality_df = pd.json_normalize(df['quality_metrics'])
            
            if 'use_reranker' in params_df.columns:
                reranker_quality = pd.DataFrame({
                    'use_reranker': params_df['use_reranker'],
                    'avg_score': quality_df['avg_score']
                })
                
                sns.boxplot(data=reranker_quality, x='use_reranker', y='avg_score', ax=axes[1, 1])
                axes[1, 1].set_title('Quality Score by Reranker Usage')
        
        plt.tight_layout()
        plt.savefig('agent_performance_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, days_back=7):
        """Generate comprehensive performance report"""
        print("🔍 Loading performance data...")
        df = self.load_quality_metrics(days_back)
        
        if df.empty:
            print("❌ No performance data found")
            return
        
        print("📊 Analyzing agent performance...")
        self.analyze_agent_performance(df)
        
        print("📈 Generating performance plots...")
        self.generate_performance_plots(df)
        
        print("✅ Performance analysis complete!")

if __name__ == "__main__":
    analyzer = AgentPerformanceAnalyzer()
    analyzer.generate_report(days_back=7)