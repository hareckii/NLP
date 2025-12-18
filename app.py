from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from methods import LanguageDetector
from database import get_session, Document, DetectionResult
import os
from datetime import datetime

app = FastAPI(title="Language Detection API", version="1.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = LanguageDetector()

@app.get("/")
async def root():
    return {"message": "Language Detection API", "status": "running"}

@app.post("/detect/")
async def detect_language(file: UploadFile = File(...)):
    """Определение языка текстового документа"""
    try:
        # Чтение файла
        content = await file.read()
        text = content.decode('utf-8')
        
        # Определение языка всеми методами
        results = detector.detect_all_methods(text)
        
        # Сохранение в базу данных
        session = get_session()
        
        doc = Document(
            filename=file.filename,
            content=text[:1000],  # Сохраняем только начало
            language_n_gram=results['n_gram']['language'],
            language_alphabet=results['alphabet']['language'],
            language_neural=results['neural']['language'],
            confidence_n_gram=results['n_gram']['confidence'],
            confidence_alphabet=results['alphabet']['confidence'],
            confidence_neural=results['neural']['confidence'],
            processing_time=sum(r['time'] for r in results.values())
        )
        
        session.add(doc)
        session.commit()
        
        # Сохраняем результаты
        for method, data in results.items():
            result = DetectionResult(
                document_id=doc.id,
                method=method,
                detected_language=data['language'],
                confidence=data['confidence'],
                processing_time=data['time']
            )
            session.add(result)
        
        session.commit()
        session.close()
        
        return {
            "filename": file.filename,
            "results": results,
            "document_id": doc.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/")
async def get_statistics():
    """Получение статистики по всем документам"""
    session = get_session()
    
    try:
        # Общая статистика
        total_docs = session.query(Document).count()
        
        # Статистика по методам
        stats = {}
        methods = ['n_gram', 'alphabet', 'neural']
        
        for method in methods:
            results = session.query(DetectionResult).filter_by(method=method).all()
            if results:
                avg_confidence = sum(r.confidence for r in results) / len(results)
                avg_time = sum(r.processing_time for r in results) / len(results)
                
                stats[method] = {
                    "total_detections": len(results),
                    "average_confidence": avg_confidence,
                    "average_time": avg_time
                }
        
        session.close()
        
        return {
            "total_documents": total_docs,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/")
async def get_documents():
    """Получение списка всех документов"""
    session = get_session()
    
    try:
        documents = session.query(Document).all()
        result = []
        
        for doc in documents:
            result.append({
                "id": doc.id,
                "filename": doc.filename,
                "timestamp": doc.created_at.isoformat(),
                "languages": {
                    "n_gram": doc.language_n_gram,
                    "alphabet": doc.language_alphabet,
                    "neural": doc.language_neural
                }
            })
        
        session.close()
        return result
        
    except Exception as e:
        session.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)