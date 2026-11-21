import 'package:flutter/material.dart';
import '../../api/api.dart';
import '../../data/session.dart';
import '../../shell/shell.dart';
import '../../theme/tokens.dart';

const _roles = [
  ('nurse', 'Nurse', 'eCRF + review'),
  ('monitor', 'Monitor', 'Read-only SDV'),
  ('pi', 'PI', 'Study + export'),
];

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  String role = 'nurse';
  final user = TextEditingController(text: 'nurse');
  final pass = TextEditingController();
  bool busy = false, reveal = false;
  bool? healthy;
  String? error;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (healthy == null) {
      SessionScope.read(context).ping().then((ok) {
        if (mounted) setState(() => healthy = ok);
      });
    }
  }

  void _pick(String r) => setState(() {
        role = r;
        user.text = r; // demo accounts are named after the role
      });

  Future<void> _submit() async {
    final s = SessionScope.read(context);
    setState(() { busy = true; error = null; });
    try {
      await s.login(user.text.trim(), pass.text, roleHint: role);
    } on ApiException {
      if (mounted) setState(() { busy = false; error = 'We could not sign you in. Check your username and password.'; });
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: K.surface,
        body: Column(children: [
          const SyntheticBanner(),
          Expanded(
            child: LayoutBuilder(builder: (_, box) {
              final split = box.maxWidth >= 1000;
              return Row(children: [
                if (split) Expanded(flex: 44, child: _brand()),
                Expanded(flex: 56, child: Center(child: SingleChildScrollView(padding: const EdgeInsets.all(K.s24), child: _form()))),
              ]);
            }),
          ),
        ]),
      );

  Widget _brand() => Container(
        color: const Color(0xFF0E1B2C),
        padding: const EdgeInsets.all(48),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Row(children: [
            Icon(Icons.hub_outlined, color: Colors.white, size: 28),
            SizedBox(width: 12),
            Text('Yammic', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w500, letterSpacing: -.3)),
          ]),
          const Spacer(),
          const Text('Clinical research,\nconnected.', style: TextStyle(color: Colors.white, fontSize: 40, height: 1.15, fontWeight: FontWeight.w500, letterSpacing: -.5)),
          const SizedBox(height: 16),
          const Text('One connected record, from hospital data to regulator-ready evidence. AI proposes. People verify.', style: TextStyle(color: Color(0xFF9FB3C8), fontSize: 15, height: 1.5)),
          const Spacer(),
          Row(children: [
            Icon(healthy == false ? Icons.cloud_off : Icons.circle, size: 10, color: healthy == false ? const Color(0xFF9FB3C8) : const Color(0xFF3CC4C4)),
            const SizedBox(width: 8),
            Text(healthy == null ? 'Checking local backend…' : healthy! ? 'Local backend healthy' : 'Local backend is down', style: const TextStyle(color: Color(0xFF9FB3C8), fontSize: 13)),
          ]),
          const SizedBox(height: 4),
          const Text('FHIR R4 · Postgres 16', style: TextStyle(color: Color(0xFF9FB3C8), fontSize: 13)),
        ]),
      );

  Widget _form() => ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: Container(
          padding: const EdgeInsets.all(40),
          decoration: BoxDecoration(color: K.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: K.line)),
          child: AutofillGroup(
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              const Text('Sign in', style: K.display),
              const SizedBox(height: 4),
              const Text('Local demo · synthetic data', style: K.small),
              const SizedBox(height: K.s24),
              if (healthy == false)
                Container(
                  margin: const EdgeInsets.only(bottom: K.s16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: K.mutedBg, borderRadius: BorderRadius.circular(8), border: Border.all(color: K.mutedLine)),
                  child: const Text('Local backend is down. Start it with `make demo`, then retry. You can still open the offline snapshot (read-only).', style: K.small),
                ),
              if (error != null)
                Container(
                  margin: const EdgeInsets.only(bottom: K.s16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: K.badBg, borderRadius: BorderRadius.circular(8), border: Border.all(color: K.badLine)),
                  child: Row(children: [
                    const Icon(Icons.error_outline, size: 18, color: K.badInk),
                    const SizedBox(width: 8),
                    Expanded(child: Text(error!, style: K.small.copyWith(color: K.badInk))),
                  ]),
                ),
              Row(children: [
                for (final r in _roles) ...[
                  Expanded(child: _RoleCard(r.$1, r.$2, r.$3, role == r.$1, () => _pick(r.$1))),
                  if (r != _roles.last) const SizedBox(width: 8),
                ],
              ]),
              const SizedBox(height: K.s24),
              TextField(controller: user, decoration: const InputDecoration(labelText: 'Username'), autofillHints: const [AutofillHints.username]),
              const SizedBox(height: K.s16),
              TextField(
                controller: pass,
                obscureText: !reveal,
                onSubmitted: (_) => _submit(),
                autofillHints: const [AutofillHints.password],
                decoration: InputDecoration(
                  labelText: 'Password',
                  suffixIcon: IconButton(
                    tooltip: reveal ? 'Hide password' : 'Show password',
                    icon: Icon(reveal ? Icons.visibility_off_outlined : Icons.visibility_outlined, size: 20),
                    onPressed: () => setState(() => reveal = !reveal),
                  ),
                ),
              ),
              const SizedBox(height: K.s24),
              SizedBox(
                height: 44,
                child: FilledButton(
                  onPressed: busy ? null : _submit,
                  child: busy
                      ? const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)),
                          SizedBox(width: 10),
                          Text('Signing in…'),
                        ])
                      : const Text('Sign in'),
                ),
              ),
              const SizedBox(height: 4),
              Row(children: [
                TextButton(onPressed: busy ? null : () { pass.text = 'demo'; _submit(); }, child: const Text('Use demo account')),
                const Spacer(),
                if (healthy == false) TextButton(onPressed: () { setState(() => healthy = null); didChangeDependencies(); }, child: const Text('Retry')),
              ]),
              const SizedBox(height: 8),
              const Text('SSO is disabled in the local demo. Demo password: demo.', style: K.small),
            ]),
          ),
        ),
      );
}

class _RoleCard extends StatelessWidget {
  final String id, name, hint;
  final bool selected;
  final VoidCallback onTap;
  const _RoleCard(this.id, this.name, this.hint, this.selected, this.onTap);
  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        selected: selected,
        label: '$name role',
        child: InkWell(
          key: ValueKey('role-$id'),
          borderRadius: BorderRadius.circular(8),
          onTap: onTap,
          child: AnimatedContainer(
            duration: K.fast,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: selected ? K.accentSoft : K.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: selected ? K.accent : K.line, width: selected ? 2 : 1),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Expanded(child: Text(name, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w500, color: K.ink))),
                if (selected) const Icon(Icons.check_circle, size: 14, color: K.accent),
              ]),
              Text(hint, style: const TextStyle(fontSize: 11.5, color: K.ink3)),
            ]),
          ),
        ),
      );
}
