from dotenv import load_dotenv
load_dotenv('.env')

from app.retrieval.vector_store import collection

result = collection.get(where={'document_name': 'control_management_guide'})

with open('chunks_debug.txt', 'w', encoding='utf-8') as f:
    f.write('Total: ' + str(len(result['ids'])) + '\n\n')
    for id_, doc in zip(result['ids'], result['documents']):
        f.write(repr(id_) + ' -> ' + repr(doc) + '\n---\n')

print('Saved to chunks_debug.txt')