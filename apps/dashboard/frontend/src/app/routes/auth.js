import { renderAuthLayout } from "../../components/layouts/auth-layout";
import { initLogin, renderLogin } from "../../features/auth/components/login";
import { navigateTo } from "../router";

export const authRoutes = [
    {
        path: '/login',
        render: () => renderAuthLayout(renderLogin()),
        init: () => initLogin(() => {
            navigateTo('/');
        })
    }
];