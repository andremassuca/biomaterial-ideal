% validar_mcdm.m: implementação independente em MATLAB do TOPSIS, WASPAS e VIKOR com critérios-alvo
% (Petković et al. 2025, eqs. 2 e 9 a 20), para comparar com os resultados do Python.
%
% Uso (na pasta do projeto): matlab -batch "run('matlab/validar_mcdm.m')"
%
% Lê os problemas de decisão dos três casos quantitativos (haste, stent e scaffold; cenários A e B) em
% app-nativa/dados/caso_*.json, gerados de data/ por scripts/exportar_app_json.py: valores típicos, tipos de
% critério, alvos e pesos (η = 1). São os mesmos dados que o núcleo Rust usa. Calcula C (TOPSIS), Q (WASPAS)
% e P (VIKOR) e compara com results/pontuacoes.csv (gerado pelo Python, scripts/run_all.py).
% Critério: diferença máxima abaixo de 1e-6. Grava results/validacao_matlab.md.

raiz = fileparts(fileparts(mfilename('fullpath')));
casos = {'haste', 'Haste'; 'stent', 'Stent'; 'scaffold', 'Scaffold'};
ref = readtable(fullfile(raiz, 'results', 'pontuacoes.csv'), 'TextType', 'string', 'Encoding', 'UTF-8', ...
    'Delimiter', ',');
LIMITE = 1e-6;

linhas = {};
dmax_total = 0;
n_total = 0;
for k = 1:size(casos, 1)
    d = jsondecode(fileread(fullfile(raiz, 'app-nativa', 'dados', ['caso_' casos{k, 1} '.json']), ...
        'Encoding', 'UTF-8'));
    cenarios = fieldnames(d.cenarios);
    for c = 1:numel(cenarios)
        p = d.cenarios.(cenarios{c});
        X = p.x_tipico;
        tipos = cellstr(p.tipos);
        alvos = p.alvos;              % null no JSON passa a NaN
        w = p.pesos(:)';
        C = topsis_alvo(X, w, tipos, alvos);
        Q = waspas_alvo(X, w, tipos, alvos, 0.5);
        P = vikor_alvo(X, w, tipos, alvos, 0.5);
        alt = string(p.alternativas);
        r = ref(ref.caso == casos{k, 2} & ref.cenario == string(cenarios{c}), :);
        if height(r) ~= numel(alt)
            error('Número de materiais diferente em %s %s: %d no JSON, %d no CSV', casos{k, 2}, ...
                cenarios{c}, numel(alt), height(r));
        end
        [~, idx] = ismember(alt, r.material);
        if any(idx == 0)
            error('Material sem par no CSV em %s %s', casos{k, 2}, cenarios{c});
        end
        dC = max(abs(C - r.C_TOPSIS(idx)));
        dQ = max(abs(Q - r.Q_WASPAS(idx)));
        dP = max(abs(P - r.P_VIKOR(idx)));
        dmax = max([dC, dQ, dP]);
        dmax_total = max(dmax_total, dmax);
        n_total = n_total + numel(alt);
        linhas{end + 1} = strrep(sprintf('| %s | %s | %d | %.1e | %.1e | %.1e |', casos{k, 2}, cenarios{c}, ...
            numel(alt), dC, dQ, dP), '.', ','); %#ok<SAGROW>
    end
end

passa = dmax_total < LIMITE;
fprintf('Diferença máxima: %.3e (%d materiais em 6 cenários); critério %.0e: %s\n', dmax_total, n_total, ...
    LIMITE, string(passa));

f = fopen(fullfile(raiz, 'results', 'validacao_matlab.md'), 'w', 'n', 'UTF-8');
fprintf(f, '# Validação em MATLAB do TOPSIS, WASPAS e VIKOR\n\n');
fprintf(f, ['Gerado por matlab/validar_mcdm.m (%s). Implementação independente dos três métodos com ' ...
    'critérios-alvo (Petković et al. 2025), sobre os mesmos problemas de decisão (app-nativa/dados/caso_*.json, ' ...
    'gerados de data/), comparada com results/pontuacoes.csv (Python).\n\n'], version);
fprintf(f, '| Caso | Cenário | Materiais | Diferença máx. em C (TOPSIS) | em Q (WASPAS) | em P (VIKOR) |\n');
fprintf(f, '|---|---|---|---|---|---|\n');
fprintf(f, '%s\n', linhas{:});
if passa
    veredicto = 'Cumpre.';
else
    veredicto = 'NÃO CUMPRE.';
end
fprintf(f, '\nDiferença máxima em todos os casos: %s (%d materiais). Critério: abaixo de 1e-6. %s\n', ...
    strrep(sprintf('%.1e', dmax_total), '.', ','), n_total, veredicto);
fclose(f);

if ~passa
    error('A validação em MATLAB não cumpre o critério (%.3e).', dmax_total);
end

% ----------------------------------------------------------------------------------------- funções

function T = referencia(x, tipo, alvo)
% Valor de referência T_j: máximo (benefício), mínimo (custo) ou o alvo.
switch tipo
    case 'benefit', T = max(x);
    case 'cost', T = min(x);
    case 'target', T = alvo;
    otherwise, error('Tipo de critério desconhecido: %s', tipo);
end
end

function C = topsis_alvo(X, w, tipos, alvos)
% TOPSIS com a normalização da eq. 2: r = 1 - |x - T| / (max(xmax, T) - min(xmin, T)).
[m, n] = size(X);
R = ones(m, n);
for j = 1:n
    x = X(:, j);
    T = referencia(x, tipos{j}, alvos(j));
    den = max(max(x), T) - min(min(x), T);
    if den ~= 0
        R(:, j) = 1 - abs(x - T) / den;
    end
end
V = R .* w;
dpos = sqrt(sum((V - max(V, [], 1)) .^ 2, 2));
dneg = sqrt(sum((V - min(V, [], 1)) .^ 2, 2));
C = dneg ./ (dpos + dneg);
end

function Q = waspas_alvo(X, w, tipos, alvos, lambda)
% WASPAS com a normalização das eqs. 9 a 13 (e os casos de fronteira do Python).
R = zeros(size(X));
for j = 1:size(X, 2)
    x = X(:, j);
    lo = min(x);
    hi = max(x);
    t = tipos{j};
    T = referencia(x, t, alvos(j));
    if strcmp(t, 'benefit') || (strcmp(t, 'target') && T == hi)
        R(:, j) = x / hi;                         % eq. 9
    elseif strcmp(t, 'cost') && lo <= 0
        if hi > 0
            R(:, j) = 1 - x / hi;                 % eq. 11 com T = 0
        else
            R(:, j) = 1;
        end
    elseif strcmp(t, 'cost') || (strcmp(t, 'target') && T == lo)
        R(:, j) = lo ./ x;                        % eq. 10
    elseif T < lo
        R(:, j) = 1 - (x - T) / hi;               % eq. 11
    elseif T > hi
        R(:, j) = 1 - (T - x) / T;                % eq. 12
    else
        R(:, j) = 1 - abs(x - T) / (hi - lo);     % eq. 13
    end
end
q1 = sum(R .* w, 2);                              % eq. 14
q2 = prod(R .^ w, 2);                             % eq. 15
Q = lambda * q1 + (1 - lambda) * q2;              % eq. 16
end

function P = vikor_alvo(X, w, tipos, alvos, v)
% VIKOR abrangente (eqs. 17 a 19), com A_j igual ao intervalo que inclui o alvo.
n = size(X, 2);
T = zeros(1, n);
for j = 1:n
    T(j) = referencia(X(:, j), tipos{j}, alvos(j));
end
A = max(max(X, [], 1), T) - min(min(X, [], 1), T);
A(A == 0) = 1;
E = w .* (1 - exp(-abs(X - T) ./ A));
S = sum(E, 2);
R = max(E, [], 2);
iguais = @(a, b) abs(a - b) <= 1e-8 + 1e-5 * abs(b);   % como numpy.isclose
sc = iguais(max(S), min(S));
rc = iguais(max(R), min(R));
if sc && rc
    P = zeros(size(S));
elseif sc
    P = (R - min(R)) / (max(R) - min(R));
elseif rc
    P = (S - min(S)) / (max(S) - min(S));
else
    P = (S - min(S)) / (max(S) - min(S)) * v + (R - min(R)) / (max(R) - min(R)) * (1 - v);
end
end
