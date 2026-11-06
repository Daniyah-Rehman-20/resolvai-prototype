import SupportWorkspace from "@/components/support/support-workspace";
import styles from "@/components/support/support.module.css";

export default function SupportPage() {
  if (process.env.GITHUB_PAGES === "true" && !process.env.NEXT_PUBLIC_API_URL) {
    return (
      <main className={styles.root}>
        <header className={styles.header}>
          <div className={styles.brand}>PayResolve<span className={styles.brandAccent}>AI</span></div>
          <span className={styles.headerLabel}>PAYMENT SUPPORT</span>
        </header>
        <div className={styles.authLayout}>
          <section className={styles.intro}>
            <span className={styles.eyebrow}>CHAT · VOICE · QUERY TRACKING</span>
            <h1>A clearer path through payment problems.</h1>
            <p>Describe a failed transaction, keep your questions together, and get support guidance in one place.</p>
          </section>
          <section className={styles.authCard} aria-labelledby="setup-title">
            <span className={styles.eyebrow}>SERVICE STATUS</span>
            <h2 id="setup-title">Support is not available yet</h2>
            <p>The website is published. Account access, chat, and voice support will open once the support service is connected.</p>
            <small>This page does not collect payment details or recordings.</small>
            <a className={styles.primary} href="https://github.com/Daniyah-Rehman-20/resolvai-prototype">View project and setup guide</a>
          </section>
        </div>
      </main>
    );
  }
  return <SupportWorkspace />;
}
