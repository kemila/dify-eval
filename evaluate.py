from ragas import metrics

from dify_eval.evaluation import evaluation

# Refer to ragas https://docs.ragas.io/en/stable/concepts/metrics/index.html
DEFAULT_METRICS = [
    metrics.answer_correctness,
    metrics.answer_relevancy,
    metrics.context_precision,
    metrics.context_recall,
    metrics.faithfulness,
    metrics.answer_similarity,
    'retrieve_f1',
    'retrieve_recall', 
    'retrieve_precision',
    'retrieve_iou',
    'retrieve_ndcg',
    'retrieve_mrr',
    'retrieve_map'
]

if __name__ == "__main__":
    evaluation.evaluate_dataset_run_items(DEFAULT_METRICS)
