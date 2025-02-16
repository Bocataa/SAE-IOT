const sqlite3 = require('sqlite3');
const express = require("express");
const cors = require("cors"); // Pour autoriser les requêtes de l'extérieur
const fs = require('fs'); // Module file system
const path = require('path'); // Module path

sqlite3.verbose();

const dbname = 'database.db3';
const dbpath = path.join(__dirname, dbname);

const app = express();
const port = 3000;

app.use(cors()); // Pas de restriction d'origine

// Vérifier si la base de données existe, sinon la créer
if (!fs.existsSync(dbpath)) {
    console.log('La base de données n\'existe pas. Création de la base de données...');
    const db = new sqlite3.Database(dbpath, (err) => {
        if (err) {
            console.error('Erreur lors de la création de la base de données:', err);
        } else {
            console.log('Base de données créée avec succès.');
            db.close();
        }
    });
}

app.get('/all', (req, res) => {
    const db = new sqlite3.Database(dbname);
    const requete_user = req.query;
    
    console.log(requete_user);

    const QUERY = `SELECT * FROM sensor_data`;

    console.log(QUERY);

    db.serialize(() => {
        db.all(QUERY, [], (erreur, montableau) => {
            if (erreur) {
                throw erreur;
            }
            res.json(montableau);
            //console.log(montableau);  // Utilisation de `valeur` avec minuscule
            db.close();
        });
    });
});

app.listen(port, () => {
    console.log(`Le serveur écoute le port : ${port}!`);
});
