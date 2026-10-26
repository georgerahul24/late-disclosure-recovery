# Detector comparison on eval text

| Detector | Text | n | Sensitivity | Specificity | PPV | Family acc. | Macro-F1 |
|---|---|---|---|---|---|---|---|
| keyword | symptom-only | 180 | 10.0 | 100.0 | 100.0 | 10.0 | 23.7 |
| keyword | reworded | 180 | 0.0 | 100.0 | - | 0.0 | 10.0 |
| keyword | in-message | 1080 | 5.0 | 100.0 | 100.0 | 5.0 | 17.2 |
| tfidf | symptom-only | 180 | 96.7 | 73.3 | 87.9 | 93.3 | 86.1 |
| tfidf | reworded | 180 | 75.8 | 83.3 | 90.1 | 67.5 | 72.2 |
| tfidf | in-message | 1080 | 81.0 | 85.6 | 91.8 | 75.4 | 79.0 |
| lora[Qwen2.5-0.5B/s0] | symptom-only | 180 | 100.0 | 81.7 | 91.6 | 97.5 | 91.3 |
| lora[Qwen2.5-0.5B/s0] | reworded | 180 | 85.8 | 83.3 | 91.2 | 75.8 | 77.8 |
| lora[Qwen2.5-0.5B/s0] | in-message | 1080 | 95.0 | 82.8 | 91.7 | 89.4 | 86.7 |
| lora[Qwen2.5-0.5B/s1] | symptom-only | 180 | 95.8 | 88.3 | 94.3 | 95.0 | 92.3 |
| lora[Qwen2.5-0.5B/s1] | reworded | 180 | 88.3 | 91.7 | 95.5 | 81.7 | 84.0 |
| lora[Qwen2.5-0.5B/s1] | in-message | 1080 | 94.0 | 89.7 | 94.8 | 91.7 | 90.8 |
| lora[Qwen2.5-0.5B/s2] | symptom-only | 180 | 95.8 | 83.3 | 92.0 | 93.3 | 89.7 |
| lora[Qwen2.5-0.5B/s2] | reworded | 180 | 85.8 | 90.0 | 94.5 | 75.8 | 79.5 |
| lora[Qwen2.5-0.5B/s2] | in-message | 1080 | 90.0 | 88.3 | 93.9 | 85.3 | 85.8 |
| lora[Qwen2.5-1.5B-Instruct/s0] | symptom-only | 180 | 99.2 | 85.0 | 93.0 | 99.2 | 93.9 |
| lora[Qwen2.5-1.5B-Instruct/s0] | reworded | 180 | 84.2 | 88.3 | 93.5 | 80.8 | 82.9 |
| lora[Qwen2.5-1.5B-Instruct/s0] | in-message | 1080 | 91.1 | 86.9 | 93.3 | 89.0 | 87.9 |
| lora[Qwen2.5-1.5B-Instruct/s1] | symptom-only | 180 | 98.3 | 86.7 | 93.7 | 97.5 | 93.1 |
| lora[Qwen2.5-1.5B-Instruct/s1] | reworded | 180 | 94.2 | 83.3 | 91.9 | 86.7 | 84.1 |
| lora[Qwen2.5-1.5B-Instruct/s1] | in-message | 1080 | 96.9 | 87.2 | 93.8 | 94.6 | 91.3 |
| lora[Qwen2.5-1.5B-Instruct/s2] | symptom-only | 180 | 100.0 | 81.7 | 91.6 | 100.0 | 93.2 |
| lora[Qwen2.5-1.5B-Instruct/s2] | reworded | 180 | 90.0 | 88.3 | 93.9 | 85.0 | 86.3 |
| lora[Qwen2.5-1.5B-Instruct/s2] | in-message | 1080 | 96.4 | 82.8 | 91.8 | 95.1 | 90.5 |
| prompted[qwen2.5:7b-instruct-q8_0] | symptom-only | 180 | 94.2 | 95.0 | 97.4 | 90.8 | 91.8 |
| prompted[qwen2.5:7b-instruct-q8_0] | reworded | 180 | 64.2 | 95.0 | 96.2 | 55.8 | 71.0 |
| prompted[qwen2.5:7b-instruct-q8_0] | in-message | 1080 | 75.4 | 97.8 | 98.5 | 71.9 | 81.4 |

