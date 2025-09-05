from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

PG_DSN = "postgresql+psycopg2://postgres:example@localhost:5433/pagila"
engine = create_engine(PG_DSN, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = automap_base()
Base.prepare(autoload_with=engine)  # современный способ

Film = Base.classes.film


Film = Base.classes.film
Inventory = Base.classes.inventory
FilmActor = Base.classes.film_actor
Actor = Base.classes.actor

# Получаем несколько "родителей"
films = session.query(Film.film_id).limit(20).all()
film_ids = [f.film_id for f in films]

# N+1: для каждого фильма отдельный SELECT в inventory / film_actor / actor
for film_id in film_ids:
    # Inventory
    inv = session.query(Inventory).filter_by(film_id=film_id).limit(1).all()
    # FilmActor
    fa = session.query(FilmActor).filter_by(film_id=film_id).limit(1).all()
    # Actor (берем случайного actor_id для примера)
    actor_id = (film_id % 200) + 1
    act = session.query(Actor).filter_by(actor_id=actor_id).limit(1).all()
