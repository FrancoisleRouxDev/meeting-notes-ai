import { Link } from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

const demoActions = [
  { task: "Send the revised proposal", owner: "Maya", due: "Fri, Nov 28", source: "Line 12" },
  { task: "Confirm the launch checklist", owner: "Ethan", due: "Not stated", source: "Line 18" },
];

export default function LandingPage() {
  return (
    <div className="landing-page">
      <header className="marketing-nav">
        <Link className="brand" to="/" aria-label="Meeting Notes AI home">
          <span className="brand-mark" aria-hidden="true">m</span>
          <span>meeting<span className="brand-light">notes</span></span>
          <span className="brand-ai">AI</span>
        </Link>
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#why-meeting-notes">Why Meeting Notes</a>
        </nav>
        <div className="marketing-actions">
          <ThemeToggle />
          <Link className="text-link" to="/login">Sign in</Link>
          <Link className="button button-small" to="/register">Get started</Link>
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-dot" /> A little more clarity after every meeting</p>
            <h1>Good meetings deserve <span>great follow-through.</span></h1>
            <p className="hero-description">
              Turn a meeting transcript into a clear summary, decisions, and action items—with
              owners, dates, and a link back to the words that matter.
            </p>
            <div className="hero-actions">
              <Link className="button" to="/register">Try it free <span aria-hidden="true">→</span></Link>
              <a className="button button-quiet" href="#how-it-works">See how it works</a>
            </div>
            <p className="hero-note">Your transcript stays yours. AI suggestions are yours to review and edit.</p>
          </div>

          <div className="preview-frame" aria-label="Preview of a meeting summary and action list">
            <div className="preview-window-bar">
              <span className="window-dots" aria-hidden="true"><i /><i /><i /></span>
              <span>YOUR MEETING, MADE USEFUL</span>
              <span className="preview-status"><i /> Ready</span>
            </div>
            <div className="preview-content">
              <div className="preview-heading">
                <div>
                  <p className="preview-kicker">TUESDAY · PRODUCT</p>
                  <h2>Weekly product sync</h2>
                </div>
                <span className="preview-pill">AI notes</span>
              </div>
              <div className="preview-summary">
                <span className="preview-icon summary-icon" aria-hidden="true">✦</span>
                <div>
                  <h3>The short version</h3>
                  <p>The team aligned on the launch sequence and agreed to resolve the last onboarding issues before release.</p>
                </div>
              </div>
              <div className="preview-decision">
                <span className="preview-icon decision-icon" aria-hidden="true">✓</span>
                <div>
                  <h3>Decision</h3>
                  <p>Keep the beta open through Friday, then review feedback.</p>
                </div>
              </div>
              <div className="preview-actions-heading">
                <h3>Next up</h3><span>2 action items</span>
              </div>
              <ul className="preview-action-list">
                {demoActions.map((action) => (
                  <li key={action.task}>
                    <span className="preview-checkbox" aria-hidden="true" />
                    <div className="preview-action-copy">
                      <strong>{action.task}</strong>
                      <span>{action.owner} <i /> {action.due}</span>
                    </div>
                    <span className="preview-source">{action.source}</span>
                  </li>
                ))}
              </ul>
              <p className="preview-footnote"><span aria-hidden="true">↗</span> Each source link takes you back to the transcript.</p>
            </div>
          </div>
          <span className="hero-decoration decoration-one" aria-hidden="true" />
          <span className="hero-decoration decoration-two" aria-hidden="true" />
        </section>

        <section className="trust-strip" aria-label="Designed for useful, trustworthy notes">
          <span>Less note-taking after the meeting</span>
          <i />
          <span>More confidence in what happens next</span>
          <i />
          <span>Built for humans to review</span>
        </section>

        <section className="how-section" id="how-it-works">
          <div className="section-heading">
            <p className="eyebrow">A simple rhythm</p>
            <h2>From conversation to clear next steps.</h2>
            <p>No complicated setup. Bring the transcript; leave with a plan.</p>
          </div>
          <div className="steps-grid">
            <article className="step-card">
              <span className="step-number">01</span>
              <span className="step-illustration transcript-illustration" aria-hidden="true">
                <i /><i /><i /><i />
              </span>
              <h3>Bring your transcript</h3>
              <p>Paste your notes or upload a text, Markdown, or VTT transcript.</p>
            </article>
            <article className="step-card">
              <span className="step-number">02</span>
              <span className="step-illustration sparkle-illustration" aria-hidden="true">✳</span>
              <h3>Get the useful bits</h3>
              <p>See a summary, decisions, and action items—checked against the original text.</p>
            </article>
            <article className="step-card">
              <span className="step-number">03</span>
              <span className="step-illustration check-illustration" aria-hidden="true">✓</span>
              <h3>Make progress together</h3>
              <p>Edit owners and due dates, track progress, and jump back to the source line.</p>
            </article>
          </div>
        </section>

        <section className="reassurance-section" id="why-meeting-notes">
          <div>
            <p className="eyebrow">Useful, not unquestioned</p>
            <h2>AI helps with the reading. You stay in charge.</h2>
          </div>
          <ul>
            <li><span>✓</span> Unsupported owners and dates are left blank.</li>
            <li><span>✓</span> Every action item can link to its transcript line.</li>
            <li><span>✓</span> Edit, assign, track, or complete items whenever you need.</li>
          </ul>
        </section>

        <section className="closing-cta">
          <div>
            <p className="eyebrow">Make the next meeting count</p>
            <h2>Turn “we should” into “it’s done.”</h2>
          </div>
          <Link className="button button-light" to="/register">Create your free account <span aria-hidden="true">→</span></Link>
        </section>
      </main>

      <footer className="site-footer">
        <Link className="brand" to="/">
          <span className="brand-mark" aria-hidden="true">m</span>
          <span>meeting<span className="brand-light">notes</span></span>
          <span className="brand-ai">AI</span>
        </Link>
        <span>Thoughtful notes for what comes next.</span>
        <Link to="/login">Sign in</Link>
      </footer>
    </div>
  );
}
