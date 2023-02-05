from sgnlp.models.sentic_gcn import (
    SenticGCNBertConfig,
    SenticGCNBertModel,
    SenticGCNBertEmbeddingConfig,
    SenticGCNBertEmbeddingModel,
    SenticGCNBertTokenizer,
    SenticGCNBertPreprocessor,
    SenticGCNBertPostprocessor,
)


aspect_list = [
    "teacher",
    "professor",
    "course",
    "style",
    "lecture",
    "class",
    "environment",
    "experience",
    "man",
    "woman",
    "test",
    "exam",
    "assignment",
    "material",
    "effort",
    "comprehension",
    "grade",
    "grading",
    "notes",
    "diagram",
    "expectation",
    "textbook",
]


class ReviewSentiment:
    def __init__(self):
        self.tokenizer = SenticGCNBertTokenizer.from_pretrained("bert-base-uncased")

        self.config = SenticGCNBertConfig.from_pretrained(
            r"./prototype/senticgcnbert/config.json"
        )

        self.model = SenticGCNBertModel.from_pretrained(
            r"./prototype/senticgcnbert/pytorch_model.bin",
            config=self.config,
        )

        self.embed_config = SenticGCNBertEmbeddingConfig.from_pretrained(
            "bert-base-uncased"
        )

        self.embed_model = SenticGCNBertEmbeddingModel.from_pretrained(
            "bert-base-uncased", config=self.embed_config
        )

        self.preprocessor = SenticGCNBertPreprocessor(
            tokenizer=self.tokenizer,
            embedding_model=self.embed_model,
            senticnet="https://storage.googleapis.com/sgnlp/models/sentic_gcn/senticnet.pickle",
            device="cpu",
        )

        self.postprocessor = SenticGCNBertPostprocessor()

    def predict(self, sentence):
        aspect_in_sentence = [i for i in aspect_list if i in sentence.lower()]
        if not aspect_in_sentence:
            return []
        inputs = [
            {
                "aspects": aspect_in_sentence,
                "sentence": sentence.lower(),
            },
        ]

        processed_inputs, processed_indices = self.preprocessor(inputs)
        raw_outputs = self.model(processed_indices)

        post_outputs = self.postprocessor(
            processed_inputs=processed_inputs, model_outputs=raw_outputs
        )

        return post_outputs
