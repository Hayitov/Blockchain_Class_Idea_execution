import { http, createConfig } from "wagmi";
import { sepolia } from "wagmi/chains";
import { injected } from "wagmi/connectors";

export const wagmiConfig = createConfig({
  chains: [sepolia],
  connectors: [injected()],
  transports: {
    // The frontend never makes real RPC calls — wagmi only needs a transport
    // for chain metadata. The grader's Sepolia traffic is server-side.
    [sepolia.id]: http(),
  },
});
