// Hand-build EIP-4361 message. Avoids pulling in @web3modal/siwe for one screen.
// Format reference: https://eips.ethereum.org/EIPS/eip-4361

export function buildSiweMessage(opts: {
  domain: string;
  address: string;
  uri: string;
  chainId: number;
  nonce: string;
  statement?: string;
  issuedAt?: string;
}): string {
  const issuedAt = opts.issuedAt ?? new Date().toISOString();
  const statement = opts.statement ?? "CS423 Grading Platform — sign in to view your grades.";
  return [
    `${opts.domain} wants you to sign in with your Ethereum account:`,
    opts.address,
    "",
    statement,
    "",
    `URI: ${opts.uri}`,
    "Version: 1",
    `Chain ID: ${opts.chainId}`,
    `Nonce: ${opts.nonce}`,
    `Issued At: ${issuedAt}`,
  ].join("\n");
}
