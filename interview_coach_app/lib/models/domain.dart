class DomainModel {
  final String filename;
  final List<dynamic> topDomains;

  DomainModel({required this.filename, required this.topDomains});

  factory DomainModel.fromMap(Map<String, dynamic> m) {
    return DomainModel(
      filename: m['filename'] ?? '',
      topDomains: List<dynamic>.from(m['top_domains'] ?? []),
    );
  }
}
