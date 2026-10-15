import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, CalendarDays, MessageCircleHeart, FileText, Lock } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

const HERO = "https://images.unsplash.com/photo-1755676433268-63fcc44e190f?crop=entropy&cs=srgb&fm=jpg&q=80&w=1400";

const POINTS = [
  { icon: CalendarDays, title: "Log gently", text: "Period, flow, mood, symptoms, medications and private notes — only what feels useful." },
  { icon: FileText, title: "See patterns", text: "Estimates clearly labelled as estimates, plus personal and clinician-ready summaries you can download." },
  { icon: MessageCircleHeart, title: "Ask without judgement", text: "An empathetic chat that explains, points to trusted sources, and never diagnoses or prescribes." },
  { icon: Lock, title: "Stay private", text: "App lock, encrypted sync, full export and permanent deletion — your records, your control." },
];

export default function Landing() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  useEffect(() => { if (!loading && user) navigate("/app", { replace: true }); }, [user, loading, navigate]);

  const signIn = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/app";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen">
      <a href="#landing-main" className="sr-only-focusable fixed left-4 top-4 z-50 rounded-full bg-primary px-4 py-2 text-primary-foreground">Skip to content</a>
      <header className="flex items-center justify-between px-6 py-5 md:px-12">
        <span className="font-display text-2xl font-semibold tracking-tight" data-testid="landing-brand">ForHer</span>
        <Button onClick={signIn} variant="outline" className="rounded-full border-primary text-primary hover:bg-secondary/40" data-testid="landing-signin-top">Sign in with Google</Button>
      </header>

      <main id="landing-main" className="px-6 md:px-12">
        <section className="grid gap-10 md:grid-cols-12 md:items-center">
          <div className="md:col-span-6 fh-reveal">
            <p className="fh-eyebrow">Cycle awareness, gently</p>
            <h1 className="mt-4 text-4xl font-semibold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">Notice your patterns.<br />Keep your privacy.</h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
              ForHer is a calm place to log how your cycle feels, understand what tends to repeat, and bring a clear summary to your clinician — without alarm, diagnoses, or anyone else seeing your data.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Button onClick={signIn} size="lg" className="rounded-full px-7 transition-transform duration-200 hover:-translate-y-[1px]" data-testid="landing-signin-button">Continue with Google</Button>
              <p className="flex items-center gap-2 text-sm text-muted-foreground"><ShieldCheck size={16} strokeWidth={1.5} aria-hidden /> Not medical advice. Private by design.</p>
            </div>
          </div>
          <figure className="md:col-span-6 relative overflow-hidden rounded-[2rem] aspect-[4/5] sm:aspect-[5/4] md:aspect-[4/3] fh-reveal" style={{ animationDelay: "120ms" }}>
            <img src={HERO} alt="Silhouette of a woman holding a crescent moon against a soft pink sky" className="h-full w-full object-cover" style={{ filter: "hue-rotate(-28deg) saturate(0.7) brightness(0.95)" }} loading="eager" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#8A4C55]/90 via-[#A05A65]/45 to-[#E5D0D3]/35" aria-hidden />
            <figcaption className="absolute bottom-6 left-6 right-6 text-white">
              <p className="font-display text-2xl sm:text-3xl font-semibold leading-tight">Every cycle is different. Yours deserves to be understood on your terms.</p>
            </figcaption>
          </figure>
        </section>

        <section className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-4" aria-label="What ForHer does">
          {POINTS.map(({ icon: Icon, title, text }, i) => (
            <article key={title} className="fh-card p-6 fh-reveal" style={{ animationDelay: `${150 + i * 80}ms` }}>
              <span className="inline-grid h-10 w-10 place-items-center rounded-full bg-secondary/50 text-primary"><Icon size={20} strokeWidth={1.5} aria-hidden /></span>
              <h2 className="mt-4 font-display text-2xl font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{text}</p>
            </article>
          ))}
        </section>

        <section className="my-20 fh-card p-8 md:p-10 md:grid md:grid-cols-12 md:gap-10" aria-labelledby="boundaries-heading">
          <div className="md:col-span-5">
            <p className="fh-eyebrow">Our boundaries</p>
            <h2 id="boundaries-heading" className="mt-3 font-display text-3xl font-semibold leading-tight">What ForHer is — and isn't</h2>
          </div>
          <ul className="mt-6 space-y-3 text-sm leading-relaxed text-muted-foreground md:col-span-7 md:mt-0">
            <li><strong className="text-foreground">An awareness tool,</strong> not a medical device or diagnostic service.</li>
            <li><strong className="text-foreground">Estimates are estimates.</strong> They pause when your context (pregnancy, postpartum, menopause) makes them unreliable.</li>
            <li><strong className="text-foreground">Questions like "could this be PCOS?"</strong> get plain-language education and a nudge to a qualified clinician — never a verdict.</li>
            <li><strong className="text-foreground">Reminders stay inside the locked app.</strong> No health details in notifications or links.</li>
          </ul>
        </section>
      </main>
      <footer className="px-6 pb-10 text-xs text-muted-foreground md:px-12">ForHer · Encrypted in transit · Export or permanently delete your data at any time · English first; Hindi, Kannada, Tamil and Malayalam coming after quality review.</footer>
    </div>
  );
}
