import { useEffect, useState } from "react";

import { Layout } from "../components/Layout";

import { FlashingClock } from "../components/FlashingClock";
import { PostcardTicket } from "../components/PostcardTicket";

import { ApiClientError, apiGet, type TicketResponse } from "../api/client";

import { EmailErrorPage } from "./EmailErrorPage";



export function TicketPage() {

  const [ticket, setTicket] = useState<TicketResponse | null>(null);

  const [deniedEmail, setDeniedEmail] = useState<string | null>(null);

  const [contactEmail, setContactEmail] = useState("leosocialchairs@gmail.com");

  const [loading, setLoading] = useState(true);



  useEffect(() => {

    apiGet<TicketResponse>("/api/v1/ticket")

      .then(setTicket)

      .catch((err: unknown) => {

        if (err instanceof ApiClientError) {

          if (err.status === 401) {

            window.location.href = "/google/login";

            return;

          }

          if (err.status === 403) {

            const email =

              typeof err.extras?.contact_email === "string"

                ? err.extras.contact_email

                : null;

            if (email) setContactEmail(email);

            apiGet<{ email: string }>("/api/v1/me")

              .then((me) => setDeniedEmail(me.email))

              .catch(() => setDeniedEmail("your account"));

            return;

          }

        }

      })

      .finally(() => setLoading(false));

  }, []);



  if (loading) {

    return (

      <Layout showLogout>

        <div className="page-center loading">Loading your ticket…</div>

      </Layout>

    );

  }



  if (deniedEmail) {

    return <EmailErrorPage email={deniedEmail} contactEmail={contactEmail} />;

  }



  if (!ticket) {

    return (

      <Layout showLogout>

        <div className="page-center banner-error">Unable to load ticket.</div>

      </Layout>

    );

  }



  return (
    <Layout showLogout>
      <div className="page-center">
        {ticket.postcard_enabled ? (
          <PostcardTicket ticket={ticket} />
        ) : (
          <div className="card card-elevated ticket-card" style={{ maxWidth: 420, width: "100%" }}>
            <div className="ticket-body">
              <h1 className="display-title ticket-title">{ticket.title}</h1>
              <div className="ticket-qr-wrap">
                <img
                  src={`data:image/png;base64,${ticket.qr_code_base64}`}
                  alt="Your event QR ticket"
                  className="ticket-qr"
                />
              </div>
              <FlashingClock />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );

}


