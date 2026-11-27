import { useState, useEffect } from "react";
import {
	fetchApiKeys,
	createApiKey,
	fetchWebhooks,
	registerWebhook,
	fetchBillingBalance,
	createBillingOrder,
	verifyPayment,
	fetchBillingUsage
} from "../services/api";

export default function DeveloperConsole() {
	const [activeTab, setActiveTab] = useState("keys"); // 'keys' | 'webhooks' | 'billing'

	// API Keys State
	const [keys, setKeys] = useState([]);
	const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
	const [keyName, setKeyName] = useState("");
	const [createdKeyData, setCreatedKeyData] = useState(null);
	const [isCopied, setIsCopied] = useState(false);

	// Webhooks State
	const [webhooks, setWebhooks] = useState([]);
	const [webhookUrl, setWebhookUrl] = useState("");
	const [webhookSuccessMsg, setWebhookSuccessMsg] = useState("");

	// Billing State
	const [billing, setBilling] = useState(null);
	const [usage, setUsage] = useState([]);
	const [billingLoading, setBillingLoading] = useState(false);
	const [purchaseSuccessMsg, setPurchaseSuccessMsg] = useState("");

	useEffect(() => {
		loadData();
	}, []);

	const loadData = async () => {
		try {
			const [kList, whList, bData, uList] = await Promise.all([
				fetchApiKeys(),
				fetchWebhooks(),
				fetchBillingBalance(),
				fetchBillingUsage()
			]);
			setKeys(kList || []);
			setWebhooks(whList || []);
			setBilling(bData);
			setUsage(uList || []);
		} catch (err) {
			console.warn("Failed to load developer portal state:", err);
		}
	};

	const handleCreateKey = async (e) => {
		e.preventDefault();
		try {
			const res = await createApiKey({ name: keyName || "API Key", scopes: ["eval:read", "eval:write"] });
			setCreatedKeyData(res);
			setKeyName("");
			const updated = await fetchApiKeys();
			setKeys(updated);
		} catch (err) {
			alert("Failed to generate key: " + err.message);
		}
	};

	const handleRegisterWebhook = async (e) => {
		e.preventDefault();
		if (!webhookUrl) return;
		try {
			await registerWebhook({ url: webhookUrl, events: ["evaluation.completed", "evaluation.failed"] });
			setWebhookUrl("");
			setWebhookSuccessMsg("Webhook endpoint registered successfully!");
			setTimeout(() => setWebhookSuccessMsg(""), 4000);
			const updated = await fetchWebhooks();
			setWebhooks(updated);
		} catch (err) {
			alert("Failed to register webhook: " + err.message);
		}
	};

	const handlePurchasePackage = async (packageId) => {
		setBillingLoading(true);
		setPurchaseSuccessMsg("");
		try {
			const order = await createBillingOrder(packageId);

			// Real Razorpay Standard Checkout integration when SDK script is loaded
			if (typeof window !== "undefined" && window.Razorpay && order.key_id && !order.key_id.startsWith("rzp_test_simulated")) {
				const rzpOptions = {
					key: order.key_id,
					amount: order.amount_paise,
					currency: order.currency || "INR",
					name: "AutoJudge",
					description: order.package_name,
					order_id: order.order_id,
					handler: async function (response) {
						try {
							setBillingLoading(true);
							const res = await verifyPayment(
								response.razorpay_order_id,
								response.razorpay_payment_id,
								response.razorpay_signature
							);
							setPurchaseSuccessMsg(`Payment fulfilled! Added ${res.credits_granted} credits.`);
							const updatedBalance = await fetchBillingBalance();
							setBilling(updatedBalance);
							const updatedUsage = await fetchBillingUsage();
							setUsage(updatedUsage);
						} catch (verifyErr) {
							alert("Payment verification failed: " + verifyErr.message);
						} finally {
							setBillingLoading(false);
						}
					},
					prefill: {
						name: "Hackathon Organizer",
						email: "organizer@example.com"
					},
					theme: {
						color: "#6366f1"
					}
				};
				const rzp = new window.Razorpay(rzpOptions);
				rzp.open();
			} else {
				// Non-production simulation mode
				const paymentId = "pay_sim_" + Math.random().toString(36).substring(2, 12);
				const signature = "sig_verified_simulated_hmac_256";
				const res = await verifyPayment(order.order_id, paymentId, signature);
				setPurchaseSuccessMsg(`Simulated payment fulfilled! Added ${res.credits_granted} credits.`);
				const updatedBalance = await fetchBillingBalance();
				setBilling(updatedBalance);
				const updatedUsage = await fetchBillingUsage();
				setUsage(updatedUsage);
			}
		} catch (err) {
			alert("Checkout failed: " + err.message);
		} finally {
			setBillingLoading(false);
		}
	};

	const copyToClipboard = (text) => {
		navigator.clipboard.writeText(text);
		setIsCopied(true);
		setTimeout(() => setIsCopied(false), 2000);
	};

	return (
		<div style={{ width: "100%", maxWidth: "1100px", margin: "0 auto" }}>
			<header style={{ marginBottom: "2rem", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "1.25rem" }}>
				<h1>Developer & Monetization Console</h1>
				<p style={{ marginTop: "0.25rem", color: "var(--text-secondary)" }}>
					Manage programmatic API credentials, webhook endpoints, and Razorpay evaluation credits.
				</p>
			</header>

			{/* Navigation Tabs */}
			<div style={{ display: "flex", gap: "1rem", borderBottom: "1px solid var(--border-subtle)", marginBottom: "2rem" }}>
				{[
					{ id: "keys", label: "API Keys", icon: "🔑" },
					{ id: "webhooks", label: "Webhooks", icon: "⚡" },
					{ id: "billing", label: "Credits & Billing", icon: "💳" }
				].map((tab) => (
					<button
						key={tab.id}
						onClick={() => setActiveTab(tab.id)}
						style={{
							padding: "0.75rem 1.25rem",
							background: "none",
							border: "none",
							borderBottom: activeTab === tab.id ? "2px solid var(--accent)" : "2px solid transparent",
							color: activeTab === tab.id ? "var(--accent)" : "var(--text-secondary)",
							fontWeight: 600,
							cursor: "pointer",
							fontSize: "0.95rem",
							display: "flex",
							alignItems: "center",
							gap: "0.5rem"
						}}
					>
						<span>{tab.icon}</span>
						<span>{tab.label}</span>
					</button>
				))}
			</div>

			{/* TAB 1: API KEYS */}
			{activeTab === "keys" && (
				<section>
					<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
						<div>
							<h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Cryptographic API Keys</h2>
							<p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
								Used to authenticate headless evaluation requests via <code>POST /v1/evaluations</code>.
							</p>
						</div>
						<button
							onClick={() => { setIsKeyModalOpen(true); setCreatedKeyData(null); }}
							className="btn btn-primary"
							style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}
						>
							+ Issue New API Key
						</button>
					</div>

					{/* Modal for New Key */}
					{isKeyModalOpen && (
						<div style={{
							position: "fixed",
							top: 0, left: 0, right: 0, bottom: 0,
							background: "rgba(0,0,0,0.75)",
							display: "flex",
							justifyContent: "center",
							alignItems: "center",
							zIndex: 1000
						}}>
							<div style={{
								background: "var(--bg-surface)",
								border: "1px solid var(--border-subtle)",
								borderRadius: "var(--radius-lg)",
								padding: "2rem",
								maxWidth: "500px",
								width: "90%"
							}}>
								{!createdKeyData ? (
									<form onSubmit={handleCreateKey}>
										<h3 style={{ marginBottom: "1rem" }}>Generate New API Key</h3>
										<p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
											The API key grants programmatic evaluation capabilities scoped to your organization.
										</p>
										<div style={{ marginBottom: "1.25rem" }}>
											<label style={{ display: "block", fontSize: "0.8rem", marginBottom: "0.4rem", fontWeight: 500 }}>
												Key Label
											</label>
											<input
												type="text"
												placeholder="e.g. CI/CD Pipeline Key"
												value={keyName}
												onChange={(e) => setKeyName(e.target.value)}
												required
												style={{
													width: "100%",
													padding: "0.6rem",
													background: "var(--bg-element)",
													border: "1px solid var(--border-subtle)",
													borderRadius: "var(--radius-sm)",
													color: "var(--text-primary)"
												}}
											/>
										</div>
										<div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
											<button
												type="button"
												onClick={() => setIsKeyModalOpen(false)}
												className="btn btn-secondary"
												style={{ padding: "0.5rem 1rem" }}
											>
												Cancel
											</button>
											<button type="submit" className="btn btn-primary" style={{ padding: "0.5rem 1rem" }}>
												Generate Key
											</button>
										</div>
									</form>
								) : (
									<div>
										<h3 style={{ color: "var(--success)", marginBottom: "0.5rem" }}>Key Generated Successfully!</h3>
										<div style={{
											background: "rgba(239, 68, 68, 0.1)",
											border: "1px solid rgba(239, 68, 68, 0.3)",
											padding: "0.75rem",
											borderRadius: "var(--radius-sm)",
											fontSize: "0.8rem",
											color: "#fca5a5",
											marginBottom: "1rem"
										}}>
											<strong>Security Warning:</strong> Please copy this secret now. It will never be displayed again.
										</div>
										<div style={{
											background: "var(--bg-element)",
											padding: "0.75rem",
											borderRadius: "var(--radius-sm)",
											fontFamily: "var(--mono)",
											fontSize: "0.85rem",
											wordBreak: "break-all",
											marginBottom: "1rem",
											border: "1px solid var(--border-subtle)"
										}}>
											{createdKeyData.api_key}
										</div>
										<div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
											<button
												onClick={() => copyToClipboard(createdKeyData.api_key)}
												className="btn btn-secondary"
												style={{ padding: "0.5rem 1rem" }}
											>
												{isCopied ? "Copied! ✓" : "Copy to Clipboard"}
											</button>
											<button
												onClick={() => { setIsKeyModalOpen(false); setCreatedKeyData(null); }}
												className="btn btn-primary"
												style={{ padding: "0.5rem 1rem" }}
											>
												Done
											</button>
										</div>
									</div>
								)}
							</div>
						</div>
					)}

					{/* Keys List */}
					<div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
						<table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
							<thead>
								<tr style={{ background: "var(--bg-element)", borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
									<th style={{ padding: "0.75rem 1rem" }}>Name</th>
									<th style={{ padding: "0.75rem 1rem" }}>Prefix</th>
									<th style={{ padding: "0.75rem 1rem" }}>Scopes</th>
									<th style={{ padding: "0.75rem 1rem" }}>Status</th>
									<th style={{ padding: "0.75rem 1rem" }}>Created</th>
								</tr>
							</thead>
							<tbody>
								{keys.length === 0 ? (
									<tr>
										<td colSpan={5} style={{ padding: "2rem", textAlign: "center", color: "var(--text-tertiary)" }}>
											No active API keys found. Click "+ Issue New API Key" above.
										</td>
									</tr>
								) : (
									keys.map((k) => (
										<tr key={k.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
											<td style={{ padding: "0.85rem 1rem", fontWeight: 500 }}>{k.name}</td>
											<td style={{ padding: "0.85rem 1rem", fontFamily: "var(--mono)", color: "var(--accent)" }}>{k.key_prefix}...</td>
											<td style={{ padding: "0.85rem 1rem" }}>
												{(k.scopes || []).map((s) => (
													<span key={s} style={{ fontSize: "0.7rem", background: "rgba(255,255,255,0.06)", padding: "0.2rem 0.4rem", borderRadius: "4px", marginRight: "0.3rem" }}>
														{s}
													</span>
												))}
											</td>
											<td style={{ padding: "0.85rem 1rem" }}>
												<span style={{ color: "var(--success)", fontSize: "0.75rem", fontWeight: 600 }}>Active</span>
											</td>
											<td style={{ padding: "0.85rem 1rem", color: "var(--text-tertiary)" }}>
												{new Date(k.created_at).toLocaleDateString()}
											</td>
										</tr>
									))
								)}
							</tbody>
						</table>
					</div>
				</section>
			)}

			{/* TAB 2: WEBHOOKS */}
			{activeTab === "webhooks" && (
				<section>
					<div style={{ marginBottom: "1.5rem" }}>
						<h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Partner Webhook Subscriptions</h2>
						<p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
							Receive HMAC-SHA256 signed event notifications when evaluation jobs finish or fail.
						</p>
					</div>

					{webhookSuccessMsg && (
						<div style={{ background: "rgba(34, 197, 94, 0.1)", border: "1px solid rgba(34, 197, 94, 0.3)", padding: "0.75rem", borderRadius: "var(--radius-sm)", color: "var(--success)", marginBottom: "1rem" }}>
							{webhookSuccessMsg}
						</div>
					)}

					<form onSubmit={handleRegisterWebhook} style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1.5rem", marginBottom: "2rem" }}>
						<h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.5rem" }}>Register Webhook Endpoint</h3>
						<div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
							<input
								type="url"
								placeholder="https://your-platform.com/api/webhooks/autojudge"
								value={webhookUrl}
								onChange={(e) => setWebhookUrl(e.target.value)}
								required
								style={{
									flex: 1,
									padding: "0.6rem 0.8rem",
									background: "var(--bg-element)",
									border: "1px solid var(--border-subtle)",
									borderRadius: "var(--radius-sm)",
									color: "var(--text-primary)"
								}}
							/>
							<button type="submit" className="btn btn-primary" style={{ padding: "0.6rem 1.25rem" }}>
								Register Endpoint
							</button>
						</div>
					</form>

					<div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
						<table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
							<thead>
								<tr style={{ background: "var(--bg-element)", borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
									<th style={{ padding: "0.75rem 1rem" }}>Endpoint URL</th>
									<th style={{ padding: "0.75rem 1rem" }}>Subscribed Events</th>
									<th style={{ padding: "0.75rem 1rem" }}>Status</th>
									<th style={{ padding: "0.75rem 1rem" }}>Registered</th>
								</tr>
							</thead>
							<tbody>
								{webhooks.length === 0 ? (
									<tr>
										<td colSpan={4} style={{ padding: "2rem", textAlign: "center", color: "var(--text-tertiary)" }}>
											No webhooks configured. Enter an endpoint above to receive signed delivery events.
										</td>
									</tr>
								) : (
									webhooks.map((wh) => (
										<tr key={wh.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
											<td style={{ padding: "0.85rem 1rem", fontFamily: "var(--mono)", color: "var(--text-primary)" }}>{wh.url}</td>
											<td style={{ padding: "0.85rem 1rem" }}>
												{(wh.events || []).map((ev) => (
													<span key={ev} style={{ fontSize: "0.7rem", background: "rgba(99, 102, 241, 0.15)", color: "var(--accent)", padding: "0.2rem 0.4rem", borderRadius: "4px", marginRight: "0.3rem" }}>
														{ev}
													</span>
												))}
											</td>
											<td style={{ padding: "0.85rem 1rem" }}>
												<span style={{ color: "var(--success)", fontSize: "0.75rem", fontWeight: 600 }}>Active</span>
											</td>
											<td style={{ padding: "0.85rem 1rem", color: "var(--text-tertiary)" }}>
												{new Date(wh.created_at).toLocaleDateString()}
											</td>
										</tr>
									))
								)}
							</tbody>
						</table>
					</div>
				</section>
			)}

			{/* TAB 3: CREDITS & BILLING */}
			{activeTab === "billing" && (
				<section>
					<div style={{ marginBottom: "1.5rem" }}>
						<h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Prepaid Evaluation Credits & Billing</h2>
						<p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
							AutoJudge meters submission evaluations (1 evaluation = 1 credit). Powered by Razorpay.
						</p>
					</div>

					{purchaseSuccessMsg && (
						<div style={{ background: "rgba(34, 197, 94, 0.1)", border: "1px solid rgba(34, 197, 94, 0.3)", padding: "0.75rem", borderRadius: "var(--radius-sm)", color: "var(--success)", marginBottom: "1.5rem" }}>
							{purchaseSuccessMsg}
						</div>
					)}

					{/* Balance Card */}
					<div style={{
						display: "grid",
						gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
						gap: "1rem",
						marginBottom: "2rem"
					}}>
						<div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1.25rem" }}>
							<span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Available Balance</span>
							<div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--accent)", marginTop: "0.3rem" }}>
								{billing?.balance || 0.0} <span style={{ fontSize: "1rem", fontWeight: 500 }}>credits</span>
							</div>
						</div>
						<div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1.25rem" }}>
							<span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Total Purchased</span>
							<div style={{ fontSize: "1.5rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "0.3rem" }}>
								{billing?.total_purchased || 0.0}
							</div>
						</div>
						<div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: "1.25rem" }}>
							<span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Total Consumed</span>
							<div style={{ fontSize: "1.5rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "0.3rem" }}>
								{billing?.total_consumed || 0.0}
							</div>
						</div>
					</div>

					{/* Purchase Packages */}
					<h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1rem" }}>Top Up Credits via Razorpay</h3>
					<div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1.25rem", marginBottom: "2.5rem" }}>
						{[
							{ id: "starter_100", name: "Team / Bootcamp Pack", price: "₹499", credits: 100, costPer: "₹4.99/eval" },
							{ id: "pro_500", name: "Organizer Pro Pack", price: "₹1,999", credits: 500, costPer: "₹3.99/eval", popular: true },
							{ id: "enterprise_2000", name: "Enterprise Pass", price: "₹5,999", credits: 2000, costPer: "₹2.99/eval" }
						].map((pkg) => (
							<div
								key={pkg.id}
								style={{
									background: "var(--bg-surface)",
									border: pkg.popular ? "2px solid var(--accent)" : "1px solid var(--border-subtle)",
									borderRadius: "var(--radius-lg)",
									padding: "1.5rem",
									display: "flex",
									flexDirection: "column",
									justifyContent: "space-between",
									position: "relative"
								}}
							>
								{pkg.popular && (
									<span style={{
										position: "absolute",
										top: "-10px",
										right: "15px",
										background: "var(--accent)",
										color: "#fff",
										fontSize: "0.7rem",
										padding: "0.2rem 0.6rem",
										borderRadius: "12px",
										fontWeight: 600
									}}>
										Most Popular
									</span>
								)}
								<div>
									<h4 style={{ fontSize: "1.05rem", fontWeight: 600 }}>{pkg.name}</h4>
									<div style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0.75rem 0 0.25rem 0", color: "var(--text-primary)" }}>
										{pkg.price}
									</div>
									<div style={{ fontSize: "0.8rem", color: "var(--accent)", fontWeight: 500, marginBottom: "1rem" }}>
										{pkg.credits} evaluation credits ({pkg.costPer})
									</div>
								</div>
								<button
									onClick={() => handlePurchasePackage(pkg.id)}
									disabled={billingLoading}
									className="btn btn-primary"
									style={{ width: "100%", padding: "0.6rem", fontSize: "0.875rem" }}
								>
									{billingLoading ? "Processing..." : `Purchase for ${pkg.price}`}
								</button>
							</div>
						))}
					</div>

					{/* Usage Audit Ledger */}
					<h3 style={{ fontSize: "1.1rem", fontWeight: 600, marginBottom: "1rem" }}>Credit Consumption Ledger</h3>
					<div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
						<table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
							<thead>
								<tr style={{ background: "var(--bg-element)", borderBottom: "1px solid var(--border-subtle)", textAlign: "left" }}>
									<th style={{ padding: "0.75rem 1rem" }}>Submission ID</th>
									<th style={{ padding: "0.75rem 1rem" }}>Credits Deducted</th>
									<th style={{ padding: "0.75rem 1rem" }}>Post Balance</th>
									<th style={{ padding: "0.75rem 1rem" }}>Reason</th>
									<th style={{ padding: "0.75rem 1rem" }}>Timestamp</th>
								</tr>
							</thead>
							<tbody>
								{usage.length === 0 ? (
									<tr>
										<td colSpan={5} style={{ padding: "2rem", textAlign: "center", color: "var(--text-tertiary)" }}>
											No usage records logged yet. Run an evaluation to record deductions.
										</td>
									</tr>
								) : (
									usage.map((u) => (
										<tr key={u.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
											<td style={{ padding: "0.85rem 1rem", fontFamily: "var(--mono)", color: "var(--accent)" }}>{u.submission_id || "-"}</td>
											<td style={{ padding: "0.85rem 1rem", color: "var(--text-primary)" }}>-{u.credits_deducted}</td>
											<td style={{ padding: "0.85rem 1rem", fontWeight: 500 }}>{u.balance_after}</td>
											<td style={{ padding: "0.85rem 1rem", color: "var(--text-secondary)" }}>{u.reason}</td>
											<td style={{ padding: "0.85rem 1rem", color: "var(--text-tertiary)" }}>
												{new Date(u.created_at).toLocaleString()}
											</td>
										</tr>
									))
								)}
							</tbody>
						</table>
					</div>
				</section>
			)}
		</div>
	);
}
