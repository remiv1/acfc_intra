from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapped_column

Base = declarative_base()

class QueueItem(Base):
    __tablename__ = 'queue'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = mapped_column(String, nullable=False)
    categorie = mapped_column(String, default='general')
    processed = mapped_column(Boolean, default=False)
    created_at = mapped_column(String, default='CURRENT_TIMESTAMP')
    created_by = mapped_column(String, default='system')
    updated_at = mapped_column(String, onupdate='CURRENT_TIMESTAMP')
    updated_by = mapped_column(String, default='system')
    result = mapped_column(String, nullable=True)


# Configuration de la base de données SQLite
engine = create_engine('sqlite:///queue.db')
Base.metadata.create_all(engine)

# Création d'une session
Session = sessionmaker(bind=engine)
session = Session()

# Exemple d'ajout d'une tâche
def add_task(task_name: str, *, created_by: str, categorie: Optional[str]) -> bool:
    try:
        task = QueueItem(task_name=task_name,
                         created_by=created_by,
                         categorie=categorie)
        session.add(task)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False

# Exemple de récupération de la prochaine tâche non traitée
def get_next_task() -> QueueItem | None:
    task = session.query(QueueItem).filter_by(processed=False).first()
    return task if task else None

# Exemple de marquage d'une tâche comme traitée
def mark_task_processed(task_id: int) -> bool:
    task = session.query(QueueItem).get(task_id)
    if task:
        task.processed = True
        session.commit()
        return True
    return False

# Exemple d'utilisation
if __name__ == "__main__":
    add_task("Task 1", created_by="admin", categorie="email")
    add_task("Task 2", created_by="admin", categorie="general")

    next_task = get_next_task()
    if next_task:
        mark_task_processed(next_task.id)
        