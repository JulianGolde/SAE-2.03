# Permet d'utiliser PyMySQL comme remplaçant de mysqlclient si ce dernier
# n'est pas installé (utile sous Windows si la compilation de mysqlclient échoue).
try:
    import MySQLdb  # noqa: F401  (mysqlclient présent : rien à faire)
except ImportError:
    try:
        import pymysql

        pymysql.install_as_MySQLdb()
    except ImportError:
        # Aucun connecteur MySQL installé : Django lèvera une erreur claire au
        # moment de la connexion. Voir requirements.txt / README.
        pass
