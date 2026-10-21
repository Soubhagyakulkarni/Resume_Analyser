"""Integration test for the analysis-to-recommendation workflow."""


def test_analysis_flows_into_recommendations(sample_analysis, sample_job):
    from services.analysis_service import AnalysisService
    from services.recommendation_service import RecommendationService

    class Gateway:
        def analyze(self, resume_text):
            return sample_analysis

    class Repository:
        def list_active_jobs(self):
            return [sample_job]

    analysis = AnalysisService(Gateway()).analyze("Built a Python data project")
    recommendations = RecommendationService(Repository()).recommend(analysis)

    assert recommendations[0].job.id == sample_job.id
    assert recommendations[0].match_ratio == 0.5
