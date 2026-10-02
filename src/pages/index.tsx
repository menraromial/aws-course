import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import styles from './index.module.css';

const CHAPITRES = [
  {num: 'Module 1', titre: 'Introduction à AWS', resume: 'Modèles de service, responsabilité partagée, catalogue, régions et zones, tarification.', to: '/cours/module-1/cours'},
  {num: 'Module 2', titre: 'Sécurité et gestion des accès', resume: 'IAM : identités, rôles, stratégies et leur évaluation. VPC, sous-réseaux, Security Groups.', to: '/cours/module-2/cours'},
  {num: 'Module 3', titre: 'Calcul : Amazon EC2', resume: "Types d'instances, AMI, EBS, clés SSH, cycle de vie, user data, IMDS. Un serveur web en ligne.", to: '/cours/module-3/cours'},
  {num: 'Module 4', titre: 'Stockage, bases de données et messages', resume: 'S3 en détail, EBS et EFS, RDS et DynamoDB, files SQS.', to: '/cours/module-4/cours'},
  {num: 'Module 5', titre: 'Projet final', resume: 'Une application publique sur EC2, adossée à S3, sans aucune clé.', to: '/cours/module-5/projet'},
];

function Hero() {
  return (
    <header className={styles.hero}>
      <div className="container">
        <div className={styles.kicker}>Cours d'introduction · 5 modules</div>
        <h1 className={styles.title}>
          Introduction à AWS
          <br />
          <span>de la console à l'application en ligne</span>
        </h1>
        <p className={styles.lead}>
          Une machine virtuelle, un bucket, un rôle, un pare-feu : à la fin du cours, votre
          application est en ligne, et vous savez expliquer chacune de ses pièces.
        </p>
        <div className={styles.actions}>
          <Link className="button button--primary button--lg" to="/cours">
            Commencer le cours
          </Link>
        </div>
      </div>
    </header>
  );
}

function Chapitres() {
  return (
    <section className={styles.section}>
      <div className="container">
        <h2 className={styles.h2}>Cinq modules</h2>
        <div className={styles.grid3}>
          {CHAPITRES.map((c) => {
            const contenu = (
              <>
                <div className={styles.cardNum}>{c.num}</div>
                <h3>{c.titre}</h3>
                <p>{c.resume}</p>
                <div className={styles.cardFoot}>{c.to ? 'Cours et TP' : 'En préparation'}</div>
              </>
            );
            return c.to ? (
              <Link key={c.num} to={c.to} className={styles.card}>{contenu}</Link>
            ) : (
              <div key={c.num} className={styles.card}>{contenu}</div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout
      title="Accueil"
      description="Cours d'introduction à AWS : IAM, EC2, S3, SQS, et un projet final déployé sur Internet.">
      <Hero />
      <main>
        <Chapitres />
      </main>
    </Layout>
  );
}
