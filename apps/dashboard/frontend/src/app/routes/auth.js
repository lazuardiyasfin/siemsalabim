import { renderAuthLayout } from "../../components/layouts/auth-layout";
import { renderLogin } from "../../features/auth/components/login";

export const authRoutes = [
    {
        path: '/login',
        render: () => renderAuthLayout(renderLogin())
    }
];