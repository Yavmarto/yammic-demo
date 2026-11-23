import 'package:flutter/material.dart';

import '../../api/api.dart';
import '../../data/session.dart';
import '../../theme/tokens.dart';

const _version = 'v0.9.1';
const _catalog =
    'https://a2ui.org/specification/v0_9_1/catalogs/basic/catalog.json';

/// Validates the supported A2UI subset before any server content is mounted.
class AssistantSurface {
  final String id;
  final Map<String, Map> components;
  AssistantSurface(this.id, this.components);

  factory AssistantSurface.parse(dynamic response) {
    Never invalid() =>
        throw const FormatException('Invalid assistant response');
    if (response is! Map || response['messages'] is! List) invalid();
    final messages = response['messages'] as List;
    String? id;
    final components = <String, Map>{};
    for (final message in messages) {
      if (message is! Map || message['version'] != _version) invalid();
      if (message.containsKey('createSurface')) {
        final create = message['createSurface'];
        if (id != null ||
            create is! Map ||
            create['surfaceId'] is! String ||
            (create['surfaceId'] as String).isEmpty ||
            create['catalogId'] != _catalog) {
          invalid();
        }
        id = create['surfaceId'] as String;
      } else if (message.containsKey('updateComponents')) {
        final update = message['updateComponents'];
        if (id == null ||
            update is! Map ||
            update['surfaceId'] != id ||
            update['components'] is! List) {
          invalid();
        }
        for (final component in update['components'] as List) {
          if (component is! Map ||
              component['id'] is! String ||
              (component['id'] as String).isEmpty ||
              !['Column', 'Text', 'Button'].contains(component['component'])) {
            invalid();
          }
          components[component['id'] as String] = component;
        }
      } else {
        invalid();
      }
    }
    if (id == null || !components.containsKey('root')) invalid();
    final visiting = <String>{};
    void validate(String key) {
      final c = components[key];
      if (c == null || !visiting.add(key)) invalid();
      switch (c['component']) {
        case 'Text':
          if (c['text'] is! String) invalid();
        case 'Column':
          if (c['children'] is! List) invalid();
          for (final child in c['children'] as List) {
            if (child is! String) invalid();
            validate(child);
          }
        case 'Button':
          final action = c['action'];
          if (c['child'] is! String ||
              action is! Map ||
              action['event'] is! Map) {
            invalid();
          }
          final event = action['event'] as Map;
          if (event['name'] is! String || event['context'] is! Map) invalid();
          validate(c['child'] as String);
          if (components[c['child']]?['component'] != 'Text') invalid();
      }
      visiting.remove(key);
    }

    validate('root');
    return AssistantSurface(id, components);
  }
}

class _Message {
  final String? text;
  final AssistantSurface? surface;
  _Message.text(this.text) : surface = null;
  _Message.surface(this.surface) : text = null;
}

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});
  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final _messages = <_Message>[];
  bool _loading = false;
  String? _error;
  String? _retryPath;
  Object? _retryBody;

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _send() {
    final text = _input.text.trim();
    if (text.isEmpty || _loading) return;
    _input.clear();
    setState(() => _messages.add(_Message.text(text)));
    _request('/assistant/turn', {'text': text});
  }

  Future<void> _request(String path, Object body) async {
    setState(() {
      _loading = true;
      _error = null;
      _retryPath = path;
      _retryBody = body;
    });
    try {
      // This read-only help endpoint is available to all authenticated roles.
      final response = await SessionScope.read(context).http.post(path, body);
      final surface = AssistantSurface.parse(response);
      if (!mounted) return;
      setState(() {
        _messages.add(_Message.surface(surface));
        _retryPath = null;
      });
    } on FormatException {
      if (mounted) {
        setState(
          () =>
              _error = 'The assistant returned an invalid response. Try again.',
        );
      }
    } on Unreachable {
      if (mounted) {
        setState(
          () => _error = 'The assistant service is unavailable. Check the local backend and try again.',
        );
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(
          () => _error = e.status < 400
              ? 'The assistant returned an invalid response. Try again.'
              : 'The assistant could not complete this request. Try again.',
        );
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (_scroll.hasClients) {
            _scroll.animateTo(
              _scroll.position.maxScrollExtent,
              duration: const Duration(milliseconds: 200),
              curve: Curves.easeOut,
            );
          }
        });
      }
    }
  }

  void _action(
    AssistantSurface surface,
    String componentId,
    Map event,
    String label,
  ) {
    if (_loading) return;
    setState(() => _messages.add(_Message.text(label)));
    _request('/assistant/action', {
      'version': _version,
      'action': {
        'name': event['name'],
        'surfaceId': surface.id,
        'sourceComponentId': componentId,
        'timestamp': DateTime.now().toUtc().toIso8601String(),
        'context': event['context'],
      },
    });
  }

  Widget _component(AssistantSurface surface, String id) {
    final c = surface.components[id]!;
    switch (c['component']) {
      case 'Text':
        return Text(
          c['text'] as String,
          style: const TextStyle(fontSize: 15, height: 1.5, color: K.ink),
        );
      case 'Column':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final child in c['children'] as List)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _component(surface, child as String),
              ),
          ],
        );
      case 'Button':
        final label = surface.components[c['child']]!['text'] as String;
        return OutlinedButton(
          onPressed: _loading
              ? null
              : () => _action(
                  surface,
                  id,
                  (c['action'] as Map)['event'] as Map,
                  label,
                ),
          child: Text(label),
        );
      default:
        return const SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) => Center(
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 820),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Assistant', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            const Text(
              'Ask about the synthetic study workflow.',
              style: TextStyle(color: K.ink2),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: ListView(
                controller: _scroll,
                children: [
                  if (_messages.isEmpty)
                    const Text(
                      'Ask a question, such as “How do I review a suggestion?”',
                      style: TextStyle(color: K.ink2),
                    ),
                  for (final message in _messages)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 20),
                      child: message.text != null
                          ? Align(
                              alignment: Alignment.centerRight,
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: K.accentSoft,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(message.text!),
                              ),
                            )
                          : Semantics(
                              container: true,
                              label: 'Assistant response',
                              child: _component(message.surface!, 'root'),
                            ),
                    ),
                  if (_loading)
                    Semantics(
                      liveRegion: true,
                      child: const Text('Assistant is responding…'),
                    ),
                  if (_error != null)
                    Semantics(
                      liveRegion: true,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(_error!, style: const TextStyle(color: K.ink)),
                          TextButton(
                            onPressed: _loading
                                ? null
                                : () => _request(_retryPath!, _retryBody!),
                            child: const Text('Try again'),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    enabled: !_loading,
                    maxLength: 1000,
                    minLines: 1,
                    maxLines: 3,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      labelText: 'Workflow question',
                      hintText: 'Ask about the study workflow',
                      border: OutlineInputBorder(),
                      counterText: '',
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton(
                  onPressed: _loading ? null : _send,
                  child: const Text('Send'),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}
